"""IMU-based odometry publisher node.

Subscribes to /livox/imu (sensor_msgs/Imu), integrates angular velocity into
orientation, then publishes nav_msgs/Odometry on /odom and broadcasts the
odom->base_link TF transform.

Position is fixed at the origin (0, 0, 0). Only orientation is integrated from
the gyroscope. This avoids the unbounded drift that results from double-integrating
accelerometer noise (a->v->p). This node is intended solely to satisfy the TF tree
requirement for odom->base_link when a full LIO pipeline (e.g. Point-LIO) is not
running.

IMU measurements are first rotated from the sensor frame (laser_link) into
base_link using the extrinsic rotation declared via ROS2 parameters
(imu_roll, imu_pitch, imu_yaw in radians). This compensates for the physical
mounting orientation of the lidar/IMU unit on the robot.
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


def _rpy_to_quat(roll: float, pitch: float, yaw: float) -> np.ndarray:
    """Convert roll-pitch-yaw (radians, extrinsic XYZ) to quaternion [x, y, z, w]."""
    cr, sr = np.cos(roll / 2), np.sin(roll / 2)
    cp, sp = np.cos(pitch / 2), np.sin(pitch / 2)
    cy, sy = np.cos(yaw / 2), np.sin(yaw / 2)
    return np.array([
        sr * cp * cy - cr * sp * sy,
        cr * sp * cy + sr * cp * sy,
        cr * cp * sy - sr * sp * cy,
        cr * cp * cy + sr * sp * sy,
    ])


# ---------------------------------------------------------------------------
# Node
# ---------------------------------------------------------------------------

class ImuOdomPublisher(Node):
    """Publish odom->base_link TF and /odom topic from IMU gyroscope integration.

    Position is fixed at the origin. Only orientation is estimated.
    """

    CALIBRATION_FRAMES = 100  # number of still frames collected before integration starts

    def __init__(self) -> None:
        super().__init__('imu_odom_publisher')

        # Extrinsic rotation: IMU frame (laser_link) -> base_link
        self.declare_parameter('imu_roll',  0.0)
        self.declare_parameter('imu_pitch', 0.0)
        self.declare_parameter('imu_yaw',   0.0)
        roll  = self.get_parameter('imu_roll').value
        pitch = self.get_parameter('imu_pitch').value
        yaw   = self.get_parameter('imu_yaw').value
        self._q_imu_to_base = _rpy_to_quat(roll, pitch, yaw)
        self.get_logger().info(
            f'IMU extrinsic rotation (RPY rad): roll={roll:.4f} pitch={pitch:.4f} yaw={yaw:.4f}'
        )

        # Calibration state — collect still frames to estimate gravity direction
        self._calib_frames: list[np.ndarray] = []  # accumulated accel samples in base_link frame
        self._calibrated = False

        # Integration state (valid only after calibration)
        self._orientation = np.array([0.0, 0.0, 0.0, 1.0])  # [x, y, z, w]
        self._last_stamp: rclpy.time.Time | None = None
        self._initialized = False  # set to True when calibration completes

        # Publishers / broadcaster
        self._odom_pub = self.create_publisher(Odometry, '/odom', 10)
        self._tf_broadcaster = tf2_ros.TransformBroadcaster(self)

        # Subscriber
        self.create_subscription(Imu, '/livox/imu', self._imu_callback, 10)

        self.get_logger().info(
            f'imu_odom_publisher started, collecting {self.CALIBRATION_FRAMES} '
            'calibration frames ...'
        )

    # -----------------------------------------------------------------------
    # Callback
    # -----------------------------------------------------------------------

    def _imu_callback(self, msg: Imu) -> None:
        accel_imu = np.array([
            msg.linear_acceleration.x,
            msg.linear_acceleration.y,
            msg.linear_acceleration.z,
        ])
        accel_base = _quat_rotate(self._q_imu_to_base, accel_imu)

        # -- Calibration phase: collect still frames to determine initial orientation
        if not self._calibrated:
            self._calib_frames.append(accel_base)
            if len(self._calib_frames) < self.CALIBRATION_FRAMES:
                # Publish identity TF during calibration so RViz shows odom == base_link
                self._publish_odom(msg.header.stamp, np.zeros(3))
                return

            # Estimate gravity direction from mean acceleration
            gravity_body = np.mean(self._calib_frames, axis=0)
            gravity_norm = np.linalg.norm(gravity_body)
            if gravity_norm < 1e-3:
                self.get_logger().warn('[WARN] Calibration: gravity too small, using identity.')
                self._orientation = np.array([0.0, 0.0, 0.0, 1.0])
            else:
                # Compute quaternion that rotates gravity_body to world [0, 0, -g]
                g_world = np.array([0.0, 0.0, -1.0])
                g_hat = gravity_body / gravity_norm
                axis = np.cross(g_hat, g_world)
                axis_norm = np.linalg.norm(axis)
                if axis_norm < 1e-6:
                    # Already aligned (or anti-aligned)
                    if np.dot(g_hat, g_world) > 0:
                        self._orientation = np.array([0.0, 0.0, 0.0, 1.0])
                    else:
                        self._orientation = np.array([1.0, 0.0, 0.0, 0.0])
                else:
                    axis = axis / axis_norm
                    angle = np.arccos(np.clip(np.dot(g_hat, g_world), -1.0, 1.0))
                    self._orientation = np.array([
                        axis[0] * np.sin(angle / 2),
                        axis[1] * np.sin(angle / 2),
                        axis[2] * np.sin(angle / 2),
                        np.cos(angle / 2),
                    ])

            self._calibrated = True
            self._initialized = True
            self._last_stamp = rclpy.time.Time.from_msg(msg.header.stamp)
            self.get_logger().info('IMU calibration complete, starting odometry integration.')
            return

        # -- Integration phase
        current_stamp = rclpy.time.Time.from_msg(msg.header.stamp)

        dt = (current_stamp - self._last_stamp).nanoseconds * 1e-9
        self._last_stamp = current_stamp

        if dt <= 0.0 or dt > 1.0:
            # Skip bad dt (clock jump or first message after gap)
            return

        omega = np.array([
            msg.angular_velocity.x,
            msg.angular_velocity.y,
            msg.angular_velocity.z,
        ])
        omega = _quat_rotate(self._q_imu_to_base, omega)

        # Integrate gyroscope -> orientation only; position stays at origin
        self._orientation = _integrate_gyro(self._orientation, omega, dt)

        self._publish_odom(msg.header.stamp, omega)

    # -----------------------------------------------------------------------
    # Publish helpers
    # -----------------------------------------------------------------------

    def _publish_odom(self, stamp, omega: np.ndarray) -> None:
        ox, oy, oz, ow = self._orientation

        # nav_msgs/Odometry — position fixed at origin, only orientation is live
        odom = Odometry()
        odom.header.stamp = stamp
        odom.header.frame_id = 'odom'
        odom.child_frame_id = 'base_link'
        odom.pose.pose.orientation.x = float(ox)
        odom.pose.pose.orientation.y = float(oy)
        odom.pose.pose.orientation.z = float(oz)
        odom.pose.pose.orientation.w = float(ow)
        odom.twist.twist.angular.x = float(omega[0])
        odom.twist.twist.angular.y = float(omega[1])
        odom.twist.twist.angular.z = float(omega[2])
        self._odom_pub.publish(odom)

        # TF: odom -> base_link — translation always zero
        tf_msg = TransformStamped()
        tf_msg.header.stamp = stamp
        tf_msg.header.frame_id = 'odom'
        tf_msg.child_frame_id = 'base_link'
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
