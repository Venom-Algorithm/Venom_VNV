#!/usr/bin/env python3
"""Config-driven static and dynamic TF publisher for robot description frames."""

import math
from typing import Any

import rclpy
import yaml
from geometry_msgs.msg import TransformStamped
from rclpy.node import Node
from tf2_ros import StaticTransformBroadcaster, TransformBroadcaster
from venom_serial_driver.msg import RobotStatus


def quaternion_from_euler(roll: float, pitch: float, yaw: float) -> tuple[float, float, float, float]:
    """Convert roll, pitch, yaw to quaternion."""
    cy = math.cos(yaw * 0.5)
    sy = math.sin(yaw * 0.5)
    cp = math.cos(pitch * 0.5)
    sp = math.sin(pitch * 0.5)
    cr = math.cos(roll * 0.5)
    sr = math.sin(roll * 0.5)

    w = cr * cp * cy + sr * sp * sy
    x = sr * cp * cy - cr * sp * sy
    y = cr * sp * cy + sr * cp * sy
    z = cr * cp * sy - sr * sp * cy
    return x, y, z, w


class DynamicTfPublisher(Node):
    """Publish static and dynamic transforms described by a YAML file."""

    def __init__(self) -> None:
        super().__init__('dynamic_tf_publisher')

        self.declare_parameter('config_file', '')
        config_file = str(self.get_parameter('config_file').value)
        if not config_file:
            raise RuntimeError('Parameter "config_file" must be provided.')

        with open(config_file, 'r', encoding='utf-8') as file:
            self._config = yaml.safe_load(file) or {}

        self._dynamic_transforms = list(self._config.get('dynamic_transforms', []))
        self._latest_status = RobotStatus()

        self._tf_broadcaster = TransformBroadcaster(self)
        self._static_tf_broadcaster = StaticTransformBroadcaster(self)

        self._publish_static_transforms()

        topic = str(self._config.get('robot_status_topic', '/robot_status'))
        self.create_subscription(RobotStatus, topic, self._status_callback, 10)

        publish_rate = float(self._config.get('publish_rate', 50.0))
        self.create_timer(1.0 / publish_rate, self._publish_dynamic_transforms)

    def _status_callback(self, msg: RobotStatus) -> None:
        self._latest_status = msg

    def _publish_static_transforms(self) -> None:
        transforms = [
            self._build_transform(tf_config, stamp=None)
            for tf_config in self._config.get('static_transforms', [])
        ]
        if transforms:
            self._static_tf_broadcaster.sendTransform(transforms)

    def _publish_dynamic_transforms(self) -> None:
        if not self._dynamic_transforms:
            return

        stamp = self.get_clock().now().to_msg()
        transforms = []
        for tf_config in self._dynamic_transforms:
            angle = self._read_angle(tf_config.get('angle_source', ''))
            sign = float(tf_config.get('sign', 1.0))
            axis = str(tf_config.get('axis', 'z'))
            rotation = list(tf_config.get('rotation', [0.0, 0.0, 0.0]))

            axis_to_index = {'x': 0, 'y': 1, 'z': 2}
            if axis not in axis_to_index:
                self.get_logger().warning(f'Unsupported rotation axis "{axis}", skipping transform.')
                continue

            rotation[axis_to_index[axis]] += sign * angle
            transforms.append(self._build_transform({**tf_config, 'rotation': rotation}, stamp=stamp))

        if transforms:
            self._tf_broadcaster.sendTransform(transforms)

    def _read_angle(self, path: str) -> float:
        value: Any = self._latest_status
        for part in path.split('.'):
            if not part:
                continue
            value = getattr(value, part)
        return float(value)

    def _build_transform(self, tf_config: dict[str, Any], stamp) -> TransformStamped:
        transform = TransformStamped()
        transform.header.stamp = stamp if stamp is not None else self.get_clock().now().to_msg()
        transform.header.frame_id = tf_config['parent_frame']
        transform.child_frame_id = tf_config['child_frame']

        tx, ty, tz = tf_config.get('translation', [0.0, 0.0, 0.0])
        roll, pitch, yaw = tf_config.get('rotation', [0.0, 0.0, 0.0])
        qx, qy, qz, qw = quaternion_from_euler(float(roll), float(pitch), float(yaw))

        transform.transform.translation.x = float(tx)
        transform.transform.translation.y = float(ty)
        transform.transform.translation.z = float(tz)
        transform.transform.rotation.x = qx
        transform.transform.rotation.y = qy
        transform.transform.rotation.z = qz
        transform.transform.rotation.w = qw
        return transform


def main(args=None) -> None:
    rclpy.init(args=args)
    node = DynamicTfPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
