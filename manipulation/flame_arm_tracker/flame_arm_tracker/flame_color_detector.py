from dataclasses import dataclass
from typing import List, Optional, Tuple

import cv2
from cv_bridge import CvBridge
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from venom_manipulation_interfaces.msg import Detection2D, Detection2DArray


@dataclass
class FlameCandidate:
    detection: Detection2D
    contour: np.ndarray


class FlameColorDetector(Node):
    def __init__(self) -> None:
        super().__init__("flame_color_detector")

        self.declare_parameter("image_topic", "/camera/d435i/color/image_raw")
        self.declare_parameter("detection_topic", "/perception/detections_2d")
        self.declare_parameter("detection_array_topic", "/perception/detections_2d_array")
        self.declare_parameter("debug_mask_topic", "/perception/debug/flame_mask")
        self.declare_parameter("debug_result_topic", "/perception/debug/flame_result")
        self.declare_parameter("publish_debug_images", True)
        self.declare_parameter("class_name", "flame_picture")
        self.declare_parameter(
            "hsv_ranges",
            [
                0, 80, 80, 12, 255, 255,
                165, 80, 80, 179, 255, 255,
                13, 70, 90, 45, 255, 255,
            ],
        )
        self.declare_parameter("min_area_px", 300.0)
        self.declare_parameter("max_area_ratio", 0.50)
        self.declare_parameter("max_bbox_area_ratio", 0.45)
        self.declare_parameter("min_confidence", 0.50)
        self.declare_parameter("morph_kernel_size", 5)
        self.declare_parameter("min_aspect_ratio", 0.20)
        self.declare_parameter("max_aspect_ratio", 5.00)
        self.declare_parameter("merge_candidates", True)

        self.class_name = str(self.get_parameter("class_name").value)
        self.min_area_px = float(self.get_parameter("min_area_px").value)
        self.max_area_ratio = float(self.get_parameter("max_area_ratio").value)
        self.max_bbox_area_ratio = float(self.get_parameter("max_bbox_area_ratio").value)
        self.min_confidence = float(self.get_parameter("min_confidence").value)
        self.morph_kernel_size = int(self.get_parameter("morph_kernel_size").value)
        self.min_aspect_ratio = float(self.get_parameter("min_aspect_ratio").value)
        self.max_aspect_ratio = float(self.get_parameter("max_aspect_ratio").value)
        self.merge_candidates = bool(self.get_parameter("merge_candidates").value)
        self.publish_debug_images = bool(self.get_parameter("publish_debug_images").value)
        self.hsv_ranges = self._parse_hsv_ranges(self.get_parameter("hsv_ranges").value)

        self.bridge = CvBridge()
        self.detection_pub = self.create_publisher(
            Detection2D,
            str(self.get_parameter("detection_topic").value),
            10,
        )
        self.array_pub = self.create_publisher(
            Detection2DArray,
            str(self.get_parameter("detection_array_topic").value),
            10,
        )
        self.mask_pub = self.create_publisher(
            Image,
            str(self.get_parameter("debug_mask_topic").value),
            10,
        )
        self.result_pub = self.create_publisher(
            Image,
            str(self.get_parameter("debug_result_topic").value),
            10,
        )
        self.image_sub = self.create_subscription(
            Image,
            str(self.get_parameter("image_topic").value),
            self.image_callback,
            10,
        )

        self.get_logger().info(
            "Flame color detector ready: topic=%s ranges=%d"
            % (self.get_parameter("image_topic").value, len(self.hsv_ranges))
        )

    def image_callback(self, message: Image) -> None:
        try:
            bgr_image = self.bridge.imgmsg_to_cv2(message, desired_encoding="bgr8")
        except Exception as exc:
            self.get_logger().warn("Failed to decode image: %s" % exc)
            return

        mask = self._build_mask(bgr_image)
        candidates = self._find_candidates(mask, message.header)
        array_message = Detection2DArray()
        array_message.header = message.header
        array_message.detections = [candidate.detection for candidate in candidates]
        self.array_pub.publish(array_message)
        if candidates:
            self.detection_pub.publish(candidates[0].detection)

        if self.publish_debug_images:
            self._publish_debug_images(message, bgr_image, mask, candidates)

    def _build_mask(self, bgr_image: np.ndarray) -> np.ndarray:
        hsv_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2HSV)
        combined = np.zeros(hsv_image.shape[:2], dtype=np.uint8)
        for lower, upper in self.hsv_ranges:
            combined = cv2.bitwise_or(combined, cv2.inRange(hsv_image, lower, upper))

        kernel_size = max(1, self.morph_kernel_size)
        if kernel_size % 2 == 0:
            kernel_size += 1
        kernel = np.ones((kernel_size, kernel_size), dtype=np.uint8)
        combined = cv2.morphologyEx(combined, cv2.MORPH_OPEN, kernel)
        combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel)
        return combined

    def _find_candidates(self, mask: np.ndarray, header) -> List[FlameCandidate]:
        image_area = float(mask.shape[0] * mask.shape[1])
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        candidates: List[FlameCandidate] = []

        for contour in contours:
            area = float(cv2.contourArea(contour))
            if area < self.min_area_px or area > image_area * self.max_area_ratio:
                continue

            x, y, width, height = cv2.boundingRect(contour)
            if width <= 0 or height <= 0:
                continue
            if float(width * height) > image_area * self.max_bbox_area_ratio:
                continue
            aspect_ratio = float(width) / float(height)
            if aspect_ratio < self.min_aspect_ratio or aspect_ratio > self.max_aspect_ratio:
                continue

            fill_ratio = area / float(width * height)
            area_score = min(1.0, area / max(self.min_area_px * 8.0, 1.0))
            shape_score = min(1.0, max(0.0, fill_ratio) * 1.6)
            confidence = float(max(0.0, min(1.0, 0.65 * area_score + 0.35 * shape_score)))
            if confidence < self.min_confidence:
                continue

            detection = Detection2D()
            detection.header = header
            detection.class_name = self.class_name
            detection.confidence = confidence
            detection.center_x = float(x + width * 0.5)
            detection.center_y = float(y + height * 0.5)
            detection.size_x = float(width)
            detection.size_y = float(height)
            candidates.append(FlameCandidate(detection=detection, contour=contour))

        if self.merge_candidates and candidates:
            merged = self._merge_candidates(candidates, header, image_area)
            return [merged] if merged is not None else []

        candidates.sort(key=lambda candidate: candidate.detection.confidence, reverse=True)
        return candidates

    def _merge_candidates(
        self,
        candidates: List[FlameCandidate],
        header,
        image_area: float,
    ) -> Optional[FlameCandidate]:
        contours = [candidate.contour for candidate in candidates]
        all_points = np.vstack(contours)
        x, y, width, height = cv2.boundingRect(all_points)
        if float(width * height) > image_area * self.max_bbox_area_ratio:
            return None
        total_area = float(sum(cv2.contourArea(contour) for contour in contours))
        box_area = float(max(1, width * height))
        fill_ratio = total_area / box_area
        best_confidence = max(candidate.detection.confidence for candidate in candidates)
        confidence = float(max(0.0, min(1.0, 0.75 * best_confidence + 0.25 * min(1.0, fill_ratio * 1.5))))

        detection = Detection2D()
        detection.header = header
        detection.class_name = self.class_name
        detection.confidence = confidence
        detection.center_x = float(x + width * 0.5)
        detection.center_y = float(y + height * 0.5)
        detection.size_x = float(width)
        detection.size_y = float(height)
        return FlameCandidate(detection=detection, contour=all_points)

    def _publish_debug_images(
        self,
        source_message: Image,
        bgr_image: np.ndarray,
        mask: np.ndarray,
        candidates: List[FlameCandidate],
    ) -> None:
        mask_message = self.bridge.cv2_to_imgmsg(mask, encoding="mono8")
        mask_message.header = source_message.header
        self.mask_pub.publish(mask_message)

        result_image = bgr_image.copy()
        for index, candidate in enumerate(candidates):
            detection = candidate.detection
            x1 = int(round(detection.center_x - detection.size_x * 0.5))
            y1 = int(round(detection.center_y - detection.size_y * 0.5))
            x2 = int(round(detection.center_x + detection.size_x * 0.5))
            y2 = int(round(detection.center_y + detection.size_y * 0.5))
            color = (0, 255, 255) if index == 0 else (0, 160, 255)
            cv2.rectangle(result_image, (x1, y1), (x2, y2), color, 2)
            cv2.drawContours(result_image, [candidate.contour], -1, color, 1)
            cv2.putText(
                result_image,
                "%.2f" % detection.confidence,
                (x1, max(0, y1 - 6)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                1,
                cv2.LINE_AA,
            )

        result_message = self.bridge.cv2_to_imgmsg(result_image, encoding="bgr8")
        result_message.header = source_message.header
        self.result_pub.publish(result_message)

    @staticmethod
    def _parse_hsv_ranges(values) -> List[Tuple[np.ndarray, np.ndarray]]:
        numeric_values = [int(value) for value in values]
        if len(numeric_values) % 6 != 0:
            raise ValueError("hsv_ranges must contain h_min,s_min,v_min,h_max,s_max,v_max tuples")

        ranges: List[Tuple[np.ndarray, np.ndarray]] = []
        for index in range(0, len(numeric_values), 6):
            lower = np.array(numeric_values[index:index + 3], dtype=np.uint8)
            upper = np.array(numeric_values[index + 3:index + 6], dtype=np.uint8)
            ranges.append((lower, upper))
        return ranges


def main() -> None:
    rclpy.init()
    node: Optional[FlameColorDetector] = None
    try:
        node = FlameColorDetector()
        rclpy.spin(node)
    finally:
        if node is not None:
            node.destroy_node()
        rclpy.shutdown()
