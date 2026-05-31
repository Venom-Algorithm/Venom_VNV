from dataclasses import dataclass

import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CameraInfo, Image


@dataclass
class CameraConfig:
    width: int
    height: int
    fx: float
    fy: float
    cx: float
    cy: float
    depth_mm: int
    publish_rate_hz: float


class FakeDepthCameraPublisher(Node):
    def __init__(self) -> None:
        super().__init__("fake_depth_camera_publisher")

        self.declare_parameter("camera_info_topic", "/camera/d435i/color/camera_info")
        self.declare_parameter("depth_topic", "/camera/d435i/aligned_depth_to_color/image_raw")
        self.declare_parameter("camera_frame", "d435i_color_optical_frame")
        self.declare_parameter("width", 640)
        self.declare_parameter("height", 480)
        self.declare_parameter("fx", 615.0)
        self.declare_parameter("fy", 615.0)
        self.declare_parameter("cx", 320.0)
        self.declare_parameter("cy", 240.0)
        self.declare_parameter("depth_mm", 450)
        self.declare_parameter("publish_rate_hz", 5.0)

        self.camera_info_topic = str(self.get_parameter("camera_info_topic").value)
        self.depth_topic = str(self.get_parameter("depth_topic").value)
        self.camera_frame = str(self.get_parameter("camera_frame").value)
        self.config = CameraConfig(
            width=int(self.get_parameter("width").value),
            height=int(self.get_parameter("height").value),
            fx=float(self.get_parameter("fx").value),
            fy=float(self.get_parameter("fy").value),
            cx=float(self.get_parameter("cx").value),
            cy=float(self.get_parameter("cy").value),
            depth_mm=int(self.get_parameter("depth_mm").value),
            publish_rate_hz=float(self.get_parameter("publish_rate_hz").value),
        )

        self.camera_info_publisher = self.create_publisher(CameraInfo, self.camera_info_topic, 10)
        self.depth_publisher = self.create_publisher(Image, self.depth_topic, 10)

        period_sec = 1.0 / max(self.config.publish_rate_hz, 0.1)
        self.timer = self.create_timer(period_sec, self.publish_messages)

    def publish_messages(self) -> None:
        stamp = self.get_clock().now().to_msg()

        camera_info = CameraInfo()
        camera_info.header.stamp = stamp
        camera_info.header.frame_id = self.camera_frame
        camera_info.width = self.config.width
        camera_info.height = self.config.height
        camera_info.k = [
            self.config.fx,
            0.0,
            self.config.cx,
            0.0,
            self.config.fy,
            self.config.cy,
            0.0,
            0.0,
            1.0,
        ]
        camera_info.p = [
            self.config.fx,
            0.0,
            self.config.cx,
            0.0,
            0.0,
            self.config.fy,
            self.config.cy,
            0.0,
            0.0,
            0.0,
            1.0,
            0.0,
        ]
        camera_info.distortion_model = "plumb_bob"
        camera_info.d = [0.0, 0.0, 0.0, 0.0, 0.0]
        self.camera_info_publisher.publish(camera_info)

        depth_image = np.zeros((self.config.height, self.config.width), dtype=np.uint16)
        x_min = max(0, int(self.config.cx) - 8)
        x_max = min(self.config.width, int(self.config.cx) + 9)
        y_min = max(0, int(self.config.cy) - 8)
        y_max = min(self.config.height, int(self.config.cy) + 9)
        depth_image[y_min:y_max, x_min:x_max] = self.config.depth_mm

        image = Image()
        image.header.stamp = stamp
        image.header.frame_id = self.camera_frame
        image.height = self.config.height
        image.width = self.config.width
        image.encoding = "16UC1"
        image.is_bigendian = False
        image.step = self.config.width * 2
        image.data = depth_image.tobytes()
        self.depth_publisher.publish(image)


def main() -> None:
    rclpy.init()
    node = FakeDepthCameraPublisher()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
