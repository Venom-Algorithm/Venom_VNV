import math
from typing import Optional

import numpy as np
import rclpy
from geometry_msgs.msg import PointStamped, Vector3
from rclpy.node import Node
from rcl_interfaces.msg import SetParametersResult
from sensor_msgs.msg import CameraInfo, Image
from std_msgs.msg import Bool, String
from tf2_geometry_msgs import do_transform_point
from tf2_ros import Buffer, TransformException, TransformListener
from venom_manipulation_interfaces.msg import Detection2D, Detection2DArray, GraspTarget


class GraspTargetFusionNode(Node):
    def __init__(self) -> None:
        super().__init__("grasp_target_fusion")

        self.declare_parameter("planning_frame", "base_link")
        self.declare_parameter("camera_frame", "camera_color_optical_frame")
        self.declare_parameter("camera_info_topic", "/camera/camera/color/camera_info")
        self.declare_parameter("aligned_depth_topic", "/camera/camera/aligned_depth_to_color/image_raw")
        self.declare_parameter("detection_topic", "/perception/detections_2d")
        self.declare_parameter("detection_array_topic", "/perception/detections_2d_array")
        self.declare_parameter("grasp_target_topic", "/perception/grasp_target")
        self.declare_parameter("target_valid_topic", "/perception/target_valid")
        self.declare_parameter("debug_topic", "/perception/grasp_target_debug")
        self.declare_parameter("min_confidence", 0.7)
        self.declare_parameter("target_class", "block")
        self.declare_parameter("use_detection_header_stamp", False)
        self.declare_parameter("require_single_target", True)
        self.declare_parameter("default_target_size_xyz", [0.045, 0.045, 0.06])
        self.declare_parameter("depth_roi_half_width_px", 2)
        self.declare_parameter("max_detection_age_sec", 0.5)
        self.declare_parameter("depth_scale", 0.001)

        self.planning_frame = self.get_parameter("planning_frame").value
        self.camera_frame = self.get_parameter("camera_frame").value
        self.min_confidence = float(self.get_parameter("min_confidence").value)
        self.target_classes = set()
        self.target_class_label = "*"
        self.update_target_classes(str(self.get_parameter("target_class").value))
        self.use_detection_header_stamp = bool(
            self.get_parameter("use_detection_header_stamp").value
        )
        self.require_single_target = bool(self.get_parameter("require_single_target").value)
        self.default_target_size = self.get_parameter("default_target_size_xyz").value
        self.depth_roi_half_width_px = int(self.get_parameter("depth_roi_half_width_px").value)
        self.max_detection_age_sec = float(self.get_parameter("max_detection_age_sec").value)
        self.depth_scale = float(self.get_parameter("depth_scale").value)

        self.camera_info: Optional[CameraInfo] = None
        self.depth_image: Optional[np.ndarray] = None
        self.depth_encoding: Optional[str] = None
        self.latest_detection: Optional[Detection2D] = None
        self.latest_detection_stamp = None
        self.latest_detection_count = 0

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        self.grasp_target_publisher = self.create_publisher(
            GraspTarget,
            self.get_parameter("grasp_target_topic").value,
            10,
        )
        self.target_valid_publisher = self.create_publisher(
            Bool,
            self.get_parameter("target_valid_topic").value,
            10,
        )
        self.debug_publisher = self.create_publisher(
            String,
            self.get_parameter("debug_topic").value,
            10,
        )

        self.create_subscription(
            CameraInfo,
            self.get_parameter("camera_info_topic").value,
            self.camera_info_callback,
            10,
        )
        self.create_subscription(
            Image,
            self.get_parameter("aligned_depth_topic").value,
            self.depth_callback,
            10,
        )
        self.create_subscription(
            Detection2D,
            self.get_parameter("detection_topic").value,
            self.detection_callback,
            10,
        )
        self.create_subscription(
            Detection2DArray,
            self.get_parameter("detection_array_topic").value,
            self.detection_array_callback,
            10,
        )
        self.status_timer = self.create_timer(0.1, self.refresh_target_status)
        self.add_on_set_parameters_callback(self.parameters_callback)

    def parameters_callback(self, parameters):
        for parameter in parameters:
            if parameter.name == "target_class":
                self.update_target_classes(str(parameter.value))
                self.get_logger().info(
                    "Updated grasp target class filter to '%s'" % self.target_class_label
                )
        return SetParametersResult(successful=True)

    def update_target_classes(self, target_class_param: str) -> None:
        self.target_classes = {
            name.strip().lower()
            for name in target_class_param.split(",")
            if name.strip()
        }
        self.target_class_label = ",".join(sorted(self.target_classes)) or "*"

    def camera_info_callback(self, message: CameraInfo) -> None:
        self.camera_info = message

    def depth_callback(self, message: Image) -> None:
        if message.encoding not in ("16UC1", "32FC1"):
            self.get_logger().warn(
                f"Unsupported depth encoding '{message.encoding}', expected 16UC1 or 32FC1"
            )
            return

        if message.encoding == "16UC1":
          depth = np.frombuffer(message.data, dtype=np.uint16).reshape(message.height, message.width)
        else:
          depth = np.frombuffer(message.data, dtype=np.float32).reshape(message.height, message.width)

        self.depth_image = depth.copy()
        self.depth_encoding = message.encoding

    def detection_callback(self, message: Detection2D) -> None:
        self.latest_detection = message
        if (
            not self.use_detection_header_stamp
            or (message.header.stamp.sec == 0 and message.header.stamp.nanosec == 0)
        ):
            self.latest_detection_stamp = self.get_clock().now()
        else:
            self.latest_detection_stamp = rclpy.time.Time.from_msg(message.header.stamp)
        if self.latest_detection_count == 0:
            self.latest_detection_count = 1
        self.try_publish_grasp_target()

    def detection_array_callback(self, message: Detection2DArray) -> None:
        matching_detections = [
            detection
            for detection in message.detections
            if self.detection_matches_target_class(detection)
        ]
        self.latest_detection_count = len(matching_detections)
        if len(matching_detections) >= 1:
            selected = max(matching_detections, key=lambda detection: detection.confidence)
            self.detection_callback(selected)
        else:
            self.latest_detection = None
            self.latest_detection_stamp = None
            self.publish_target_valid(False)

    def try_publish_grasp_target(self) -> None:
        if not self.has_valid_detection():
            return

        depth_m = self.lookup_depth_meters(
            self.latest_detection.center_x,
            self.latest_detection.center_y,
        )
        if depth_m is None or not math.isfinite(depth_m) or depth_m <= 0.0:
            self.get_logger().info(
                "Grasp target debug: invalid depth at px=(%.1f, %.1f), depth=%s"
                % (
                    self.latest_detection.center_x,
                    self.latest_detection.center_y,
                    "None" if depth_m is None else f"{depth_m:.4f}",
                )
            )
            self.publish_target_valid(False)
            return

        point_in_camera = self.project_to_camera(
            self.latest_detection.center_x,
            self.latest_detection.center_y,
            depth_m,
        )
        if point_in_camera is None:
            self.get_logger().info(
                "Grasp target debug: project_to_camera failed at px=(%.1f, %.1f) depth=%.4f"
                % (
                    self.latest_detection.center_x,
                    self.latest_detection.center_y,
                    depth_m,
                )
            )
            self.publish_target_valid(False)
            return

        try:
            transform = self.tf_buffer.lookup_transform(
                self.planning_frame,
                self.camera_frame,
                rclpy.time.Time(),
            )
        except TransformException as exc:
            self.get_logger().warn(f"Grasp target debug: TF lookup failed: {exc}")
            self.publish_target_valid(False)
            return

        point_in_base = do_transform_point(point_in_camera, transform)

        debug_text = (
            "Grasp target debug: cls=%s conf=%.3f px=(%.1f, %.1f) depth=%.4f "
            "cam=(%.4f, %.4f, %.4f) base=(%.4f, %.4f, %.4f)"
            % (
                self.latest_detection.class_name,
                self.latest_detection.confidence,
                self.latest_detection.center_x,
                self.latest_detection.center_y,
                depth_m,
                point_in_camera.point.x,
                point_in_camera.point.y,
                point_in_camera.point.z,
                point_in_base.point.x,
                point_in_base.point.y,
                point_in_base.point.z,
            )
        )
        self.get_logger().info(debug_text)
        debug_message = String()
        debug_message.data = debug_text
        self.debug_publisher.publish(debug_message)

        target = GraspTarget()
        target.header.stamp = self.get_clock().now().to_msg()
        target.header.frame_id = self.planning_frame
        target.class_name = self.latest_detection.class_name
        target.confidence = self.latest_detection.confidence
        target.pose.position = point_in_base.point
        target.pose.orientation.w = 1.0
        target.size = Vector3(
            x=float(self.default_target_size[0]),
            y=float(self.default_target_size[1]),
            z=float(self.default_target_size[2]),
        )
        target.has_yaw = False
        target.yaw = 0.0

        self.grasp_target_publisher.publish(target)
        self.publish_target_valid(True)

    def has_valid_detection(self) -> bool:
        if self.camera_info is None or self.depth_image is None or self.latest_detection is None:
            missing = []
            if self.camera_info is None:
                missing.append("camera_info")
            if self.depth_image is None:
                missing.append("depth_image")
            if self.latest_detection is None:
                missing.append("latest_detection")
            self.get_logger().info(
                "Grasp target debug: waiting for %s" % ",".join(missing)
            )
            self.publish_target_valid(False)
            return False

        if self.latest_detection.confidence < self.min_confidence:
            self.get_logger().info(
                "Grasp target debug: confidence too low %.3f < %.3f"
                % (self.latest_detection.confidence, self.min_confidence)
            )
            self.publish_target_valid(False)
            return False

        if not self.detection_matches_target_class(self.latest_detection):
            self.get_logger().info(
                "Grasp target debug: class mismatch %s not in %s"
                % (self.latest_detection.class_name.lower(), self.target_class_label)
            )
            self.publish_target_valid(False)
            return False

        if self.require_single_target and self.latest_detection_count != 1:
            self.get_logger().info(
                "Grasp target debug: target count invalid %d"
                % self.latest_detection_count
            )
            self.publish_target_valid(False)
            return False

        if self.latest_detection_stamp is None:
            self.get_logger().info("Grasp target debug: detection stamp missing")
            self.publish_target_valid(False)
            return False

        age = (self.get_clock().now() - self.latest_detection_stamp).nanoseconds / 1e9
        if age > self.max_detection_age_sec:
            self.get_logger().info(
                "Grasp target debug: detection too old %.3fs > %.3fs"
                % (age, self.max_detection_age_sec)
            )
            self.publish_target_valid(False)
            return False

        return True

    def detection_matches_target_class(self, detection: Detection2D) -> bool:
        if not self.target_classes:
            return True
        return detection.class_name.strip().lower() in self.target_classes

    def refresh_target_status(self) -> None:
        self.has_valid_detection()

    def lookup_depth_meters(self, center_x: float, center_y: float) -> Optional[float]:
        if self.depth_image is None:
            return None

        x = int(round(center_x))
        y = int(round(center_y))
        if (
            x < 0
            or y < 0
            or x >= self.depth_image.shape[1]
            or y >= self.depth_image.shape[0]
        ):
            return None

        roi = self.depth_image[
            max(0, y - self.depth_roi_half_width_px): min(self.depth_image.shape[0], y + self.depth_roi_half_width_px + 1),
            max(0, x - self.depth_roi_half_width_px): min(self.depth_image.shape[1], x + self.depth_roi_half_width_px + 1),
        ]
        valid = roi[np.isfinite(roi) & (roi > 0)]
        if valid.size == 0:
            return None

        depth = float(np.median(valid))
        if self.depth_encoding == "16UC1":
            return depth * self.depth_scale
        return depth

    def project_to_camera(self, center_x: float, center_y: float, depth_m: float) -> Optional[PointStamped]:
        if self.camera_info is None:
            return None

        fx = self.camera_info.k[0]
        fy = self.camera_info.k[4]
        cx = self.camera_info.k[2]
        cy = self.camera_info.k[5]
        if fx <= 0.0 or fy <= 0.0:
            return None

        x = (center_x - cx) * depth_m / fx
        y = (center_y - cy) * depth_m / fy

        point = PointStamped()
        point.header.stamp = self.get_clock().now().to_msg()
        point.header.frame_id = self.camera_frame
        point.point.x = float(x)
        point.point.y = float(y)
        point.point.z = float(depth_m)
        return point

    def publish_target_valid(self, value: bool) -> None:
        message = Bool()
        message.data = value
        self.target_valid_publisher.publish(message)


def main() -> None:
    rclpy.init()
    node = GraspTargetFusionNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
