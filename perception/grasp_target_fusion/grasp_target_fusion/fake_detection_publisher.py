from dataclasses import dataclass

import rclpy
from rclpy.node import Node
from venom_manipulation_interfaces.msg import Detection2D, Detection2DArray


@dataclass
class DetectionConfig:
    class_name: str
    confidence: float
    center_x: float
    center_y: float
    size_x: float
    size_y: float
    publish_rate_hz: float


class FakeDetectionPublisher(Node):
    def __init__(self) -> None:
        super().__init__("fake_detection_publisher")

        self.declare_parameter("topic", "/perception/detections_2d")
        self.declare_parameter("class_name", "block")
        self.declare_parameter("confidence", 0.95)
        self.declare_parameter("center_x", 320.0)
        self.declare_parameter("center_y", 240.0)
        self.declare_parameter("size_x", 80.0)
        self.declare_parameter("size_y", 80.0)
        self.declare_parameter("publish_rate_hz", 5.0)

        self.config = DetectionConfig(
            class_name=str(self.get_parameter("class_name").value),
            confidence=float(self.get_parameter("confidence").value),
            center_x=float(self.get_parameter("center_x").value),
            center_y=float(self.get_parameter("center_y").value),
            size_x=float(self.get_parameter("size_x").value),
            size_y=float(self.get_parameter("size_y").value),
            publish_rate_hz=float(self.get_parameter("publish_rate_hz").value),
        )

        self.publisher = self.create_publisher(
            Detection2D,
            self.get_parameter("topic").value,
            10,
        )
        self.array_publisher = self.create_publisher(
            Detection2DArray,
            f"{self.get_parameter('topic').value}_array",
            10,
        )
        period_sec = 1.0 / max(self.config.publish_rate_hz, 0.1)
        self.timer = self.create_timer(period_sec, self.publish_detection)

    def publish_detection(self) -> None:
        message = Detection2D()
        message.header.stamp = self.get_clock().now().to_msg()
        message.header.frame_id = "d435i_color_optical_frame"
        message.class_name = self.config.class_name
        message.confidence = self.config.confidence
        message.center_x = self.config.center_x
        message.center_y = self.config.center_y
        message.size_x = self.config.size_x
        message.size_y = self.config.size_y
        self.publisher.publish(message)

        array_message = Detection2DArray()
        array_message.header = message.header
        array_message.detections = [message]
        self.array_publisher.publish(array_message)


def main() -> None:
    rclpy.init()
    node = FakeDetectionPublisher()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
