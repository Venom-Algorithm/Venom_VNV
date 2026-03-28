"""IMU-based odometry publisher node.

Subscribes to /livox/imu (sensor_msgs/Imu), integrates angular velocity into
orientation and linear acceleration into velocity/position, then publishes
nav_msgs/Odometry on /odom and broadcasts the odom->base_link TF transform.

This is a pure dead-reckoning node. Long-term drift is expected; it is intended
to satisfy the TF tree requirement for odom->base_link when a full LIO pipeline
(e.g. Point-LIO) is not running.
"""

import numpy as np
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import TransformStamped
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Imu
import tf2_ros


# ---------------------------------------------------------------------------
# Quaternion helpers (pure numpy, no scipy dependency)
# ---------------------------------------------------------------------------

def _quat_multiply(q1: np.ndarray, q2: np.ndarray) -> np.ndarray:
    """Multiply two quaternions [x, y, z, w]."""
    x1, y1, z1, w1 = q1
    x2, y2, z2, w2 = q2
    return np.array([
        w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
        w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
        w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
        w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
    ])


def _quat_rotate(q: np.ndarray, v: np.ndarray) -> np.ndarray:
    """Rotate vector v by quaternion q ([x, y, z, w] convention)."""
    qv = np.array([v[0], v[1], v[2], 0.0])
    q_conj = np.array([-q[0], -q[1], -q[2], q[3]])
    rotated = _quat_multiply(_quat_multiply(q, qv), q_conj)
    return rotated[:3]


def _integrate_gyro(q: np.ndarray, omega: np.ndarray, dt: float) -> np.ndarray:
    """Integrate angular velocity omega (rad/s) into quaternion q over dt seconds.

    Uses the first-order approximation:
        q_new = q + 0.5 * [omega_x, omega_y, omega_z, 0] (*) q * dt
    then normalizes.
    """
    wx, wy, wz = omega
    omega_quat = np.array([wx, wy, wz, 0.0])
    dq = 0.5 * _quat_multiply(omega_quat, q) * dt
    q_new = q + dq
    norm = np.linalg.norm(q_new)
    if norm < 1e-10:
        return np.array([0.0, 0.0, 0.0, 1.0])
    return q_new / norm


# ---------------------------------------------------------------------------
# Node
# ---------------------------------------------------------------------------

class ImuOdomPublisher(Node):
    """Publish odom->base_link TF and /odom topic from IMU integration."""

    GRAVITY = 9.81  # m/s^2

    def __init__(self) -> None:
        super().__init__('imu_odom_publisher')

        # State
        self._position = np.zeros(3)
        self._velocity = np.zeros(3)
        self._orientation = np.array([0.0, 0.0, 0.0, 1.0])  # [x, y, z, w]
        self._last_stamp: rclpy.time.Time | None = None
        self._initialized = False

        # Publishers / broadcaster
        self._odom_pub = self.create_publisher(Odometry, '/odom', 10)
        self._tf_broadcaster = tf2_ros.TransformBroadcaster(self)

        # Subscriber
        self.create_subscription(Imu, '/livox/imu', self._imu_callback, 10)

        self.get_logger().info('imu_odom_publisher started, waiting for /livox/imu ...')

    # -----------------------------------------------------------------------
    # Callback
    # -----------------------------------------------------------------------

    def _imu_callback(self, msg: Imu) -> None:
        current_stamp = rclpy.time.Time.from_msg(msg.header.stamp)

        if not self._initialized:
            self._last_stamp = current_stamp
            self._initialized = True
            return

        dt = (current_stamp - self._last_stamp).nanoseconds * 1e-9
        self._last_stamp = current_stamp

        if dt <= 0.0 or dt > 1.0:
            # Skip bad dt (clock jump or first message after gap)
            return

        # -- 1. Integrate gyroscope -> orientation
        omega = np.array([
            msg.angular_velocity.x,
            msg.angular_velocity.y,
            msg.angular_velocity.z,
        ])
        self._orientation = _integrate_gyro(self._orientation, omega, dt)

        # -- 2. Rotate body-frame acceleration to world frame
        accel_body = np.array([
            msg.linear_acceleration.x,
            msg.linear_acceleration.y,
            msg.linear_acceleration.z,
        ])
        accel_world = _quat_rotate(self._orientation, accel_body)

        # -- 3. Remove gravity (world z-up)
        accel_world[2] -= self.GRAVITY

        # -- 4. Integrate acceleration -> velocity -> position
        self._velocity += accel_world * dt
        self._position += self._velocity * dt

        # -- 5. Publish
        self._publish_odom(msg.header.stamp, omega)

    # -----------------------------------------------------------------------
    # Publish helpers
    # -----------------------------------------------------------------------

    def _publish_odom(self, stamp, omega: np.ndarray) -> None:
        ox, oy, oz, ow = self._orientation
        px, py, pz = self._position
        vx, vy, vz = self._velocity

        # nav_msgs/Odometry
        odom = Odometry()
        odom.header.stamp = stamp
        odom.header.frame_id = 'odom'
        odom.child_frame_id = 'base_link'
        odom.pose.pose.position.x = float(px)
        odom.pose.pose.position.y = float(py)
        odom.pose.pose.position.z = float(pz)
        odom.pose.pose.orientation.x = float(ox)
        odom.pose.pose.orientation.y = float(oy)
        odom.pose.pose.orientation.z = float(oz)
        odom.pose.pose.orientation.w = float(ow)
        odom.twist.twist.linear.x = float(vx)
        odom.twist.twist.linear.y = float(vy)
        odom.twist.twist.linear.z = float(vz)
        odom.twist.twist.angular.x = float(omega[0])
        odom.twist.twist.angular.y = float(omega[1])
        odom.twist.twist.angular.z = float(omega[2])
        self._odom_pub.publish(odom)

        # TF: odom -> base_link
        tf_msg = TransformStamped()
        tf_msg.header.stamp = stamp
        tf_msg.header.frame_id = 'odom'
        tf_msg.child_frame_id = 'base_link'
        tf_msg.transform.translation.x = float(px)
        tf_msg.transform.translation.y = float(py)
        tf_msg.transform.translation.z = float(pz)
        tf_msg.transform.rotation.x = float(ox)
        tf_msg.transform.rotation.y = float(oy)
        tf_msg.transform.rotation.z = float(oz)
        tf_msg.transform.rotation.w = float(ow)
        self._tf_broadcaster.sendTransform(tf_msg)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(args=None) -> None:
    """Start the imu_odom_publisher node."""
    rclpy.init(args=args)
    node = ImuOdomPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
