from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import cv2
from cv_bridge import CvBridge
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from venom_manipulation_interfaces.msg import Detection2D, Detection2DArray


@dataclass
class BoxCandidate:
    detection: Detection2D
    contour: np.ndarray
    color: Tuple[int, int, int]


class ColorBoxDetector(Node):
    def __init__(self) -> None:
        super().__init__("color_box_detector")

        self.declare_parameter("image_topic", "/camera/d435i/color/image_raw")
        self.declare_parameter("detection_topic", "/perception/detections_2d")
        self.declare_parameter("detection_array_topic", "/perception/detections_2d_array")
        self.declare_parameter("debug_mask_topic", "/perception/debug/color_box_mask")
        self.declare_parameter("debug_result_topic", "/perception/debug/color_box_result")
        self.declare_parameter("publish_debug_images", True)
        self.declare_parameter("white_class_name", "white_box")
        self.declare_parameter("black_class_name", "black_box")
        self.declare_parameter("white_hsv_ranges", [0, 0, 150, 179, 80, 255])
        self.declare_parameter("black_hsv_ranges", [0, 0, 0, 179, 255, 80])
        self.declare_parameter("min_area_px", 500.0)
        self.declare_parameter("max_area_ratio", 0.45)
        self.declare_parameter("min_confidence", 0.50)
        self.declare_parameter("morph_kernel_size", 5)
        self.declare_parameter("min_aspect_ratio", 0.35)
        self.declare_parameter("max_aspect_ratio", 3.00)

        self.white_class_name = str(self.get_parameter("white_class_name").value)
        self.black_class_name = str(self.get_parameter("black_class_name").value)
        self.min_area_px = float(self.get_parameter("min_area_px").value)
        self.max_area_ratio = float(self.get_parameter("max_area_ratio").value)
        self.min_confidence = float(self.get_parameter("min_confidence").value)
        self.morph_kernel_size = int(self.get_parameter("morph_kernel_size").value)
        self.min_aspect_ratio = float(self.get_parameter("min_aspect_ratio").value)
        self.max_aspect_ratio = float(self.get_parameter("max_aspect_ratio").value)
        self.publish_debug_images = bool(self.get_parameter("publish_debug_images").value)
        self.white_hsv_ranges = self._parse_hsv_ranges(
            self.get_parameter("white_hsv_ranges").value
        )
        self.black_hsv_ranges = self._parse_hsv_ranges(
            self.get_parameter("black_hsv_ranges").value
        )

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
        self.create_subscription(
            Image,
            str(self.get_parameter("image_topic").value),
            self.image_callback,
            10,
        )

        self.get_logger().info(
            "Color box detector ready on %s"
            % self.get_parameter("image_topic").value
        )

    def image_callback(self, message: Image) -> None:
        try:
            bgr_image = self.bridge.imgmsg_to_cv2(message, desired_encoding="bgr8")
        except Exception as exc:
            self.get_logger().warn("Failed to decode image: %s" % exc)
            return

        masks = self._build_masks(bgr_image)
        candidates: List[BoxCandidate] = []
        candidates.extend(
            self._find_candidates(
                masks[self.white_class_name],
                message.header,
                self.white_class_name,
                (255, 255, 255),
            )
        )
        candidates.extend(
            self._find_candidates(
                masks[self.black_class_name],
                message.header,
                self.black_class_name,
                (40, 40, 40),
            )
        )
        candidates.sort(key=lambda candidate: candidate.detection.confidence, reverse=True)

        array_message = Detection2DArray()
        array_message.header = message.header
        array_message.detections = [candidate.detection for candidate in candidates]
        self.array_pub.publish(array_message)
        if candidates:
            self.detection_pub.publish(candidates[0].detection)

        if self.publish_debug_images:
            self._publish_debug_images(message, bgr_image, masks, candidates)

    def _build_masks(self, bgr_image: np.ndarray) -> Dict[str, np.ndarray]:
        hsv_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2HSV)
        masks = {
            self.white_class_name: self._mask_for_ranges(hsv_image, self.white_hsv_ranges),
            self.black_class_name: self._mask_for_ranges(hsv_image, self.black_hsv_ranges),
        }
        return {class_name: self._morph(mask) for class_name, mask in masks.items()}

    @staticmethod
    def _mask_for_ranges(
        hsv_image: np.ndarray,
        ranges: List[Tuple[np.ndarray, np.ndarray]],
    ) -> np.ndarray:
        combined = np.zeros(hsv_image.shape[:2], dtype=np.uint8)
        for lower, upper in ranges:
            combined = cv2.bitwise_or(combined, cv2.inRange(hsv_image, lower, upper))
        return combined

    def _morph(self, mask: np.ndarray) -> np.ndarray:
        kernel_size = max(1, self.morph_kernel_size)
        if kernel_size % 2 == 0:
            kernel_size += 1
        kernel = np.ones((kernel_size, kernel_size), dtype=np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        return mask

    def _find_candidates(
        self,
        mask: np.ndarray,
        header,
        class_name: str,
        color: Tuple[int, int, int],
    ) -> List[BoxCandidate]:
        image_area = float(mask.shape[0] * mask.shape[1])
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        candidates: List[BoxCandidate] = []

        for contour in contours:
            area = float(cv2.contourArea(contour))
            if area < self.min_area_px or area > image_area * self.max_area_ratio:
                continue

            x, y, width, height = cv2.boundingRect(contour)
            if width <= 0 or height <= 0:
                continue
            aspect_ratio = float(width) / float(height)
            if aspect_ratio < self.min_aspect_ratio or aspect_ratio > self.max_aspect_ratio:
                continue

            fill_ratio = area / float(width * height)
            area_score = min(1.0, area / max(self.min_area_px * 8.0, 1.0))
            shape_score = min(1.0, max(0.0, fill_ratio) * 1.5)
            confidence = float(max(0.0, min(1.0, 0.60 * area_score + 0.40 * shape_score)))
            if confidence < self.min_confidence:
                continue

            detection = Detection2D()
            detection.header = header
            detection.class_name = class_name
            detection.confidence = confidence
            detection.center_x = float(x + width * 0.5)
            detection.center_y = float(y + height * 0.5)
            detection.size_x = float(width)
            detection.size_y = float(height)
            candidates.append(BoxCandidate(detection=detection, contour=contour, color=color))

        return candidates

    def _publish_debug_images(
        self,
        source_message: Image,
        bgr_image: np.ndarray,
        masks: Dict[str, np.ndarray],
        candidates: List[BoxCandidate],
    ) -> None:
        combined_mask = np.zeros(next(iter(masks.values())).shape, dtype=np.uint8)
        for mask in masks.values():
            combined_mask = cv2.bitwise_or(combined_mask, mask)
        mask_message = self.bridge.cv2_to_imgmsg(combined_mask, encoding="mono8")
        mask_message.header = source_message.header
        self.mask_pub.publish(mask_message)

        result_image = bgr_image.copy()
        for candidate in candidates:
            detection = candidate.detection
            x1 = int(round(detection.center_x - detection.size_x * 0.5))
            y1 = int(round(detection.center_y - detection.size_y * 0.5))
            x2 = int(round(detection.center_x + detection.size_x * 0.5))
            y2 = int(round(detection.center_y + detection.size_y * 0.5))
            cv2.rectangle(result_image, (x1, y1), (x2, y2), candidate.color, 2)
            cv2.drawContours(result_image, [candidate.contour], -1, candidate.color, 1)
            cv2.putText(
                result_image,
                "%s %.2f" % (detection.class_name, detection.confidence),
                (x1, max(0, y1 - 6)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                candidate.color,
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
            raise ValueError("HSV ranges must contain h_min,s_min,v_min,h_max,s_max,v_max tuples")

        ranges: List[Tuple[np.ndarray, np.ndarray]] = []
        for index in range(0, len(numeric_values), 6):
            lower = np.array(numeric_values[index:index + 3], dtype=np.uint8)
            upper = np.array(numeric_values[index + 3:index + 6], dtype=np.uint8)
            ranges.append((lower, upper))
        return ranges


def main() -> None:
    rclpy.init()
    node: Optional[ColorBoxDetector] = None
    try:
        node = ColorBoxDetector()
        rclpy.spin(node)
    finally:
        if node is not None:
            node.destroy_node()
        rclpy.shutdown()
