"""Simple Commander mission node for Scout waypoint cruising.

Features:
- Auto-discover ``waypoint.txt`` from a mounted USB drive when no path is given
- Parse CRAIC-style waypoint rows into a ``poses_list`` expressed in the map frame
- Send the full route through Nav2 Simple Commander
- Watch for local-minimum stalls and trigger spin / backup recovery behaviors
- Force-stop near the final goal by canceling Nav2 and publishing zero ``/cmd_vel``
"""

from __future__ import annotations

import math
import string
import sys
import time
from glob import glob
from pathlib import Path
from typing import List, Optional

import rclpy
from geometry_msgs.msg import PoseStamped, Twist
from nav_msgs.msg import Odometry
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from rcl_interfaces.msg import ParameterDescriptor

from venom_bringup.craic_waypoint_utils import CraicWaypoint, load_craic_waypoints


def distance_xy(x1: float, y1: float, x2: float, y2: float) -> float:
    """Return planar distance between two XY positions."""
    return math.hypot(x2 - x1, y2 - y1)


class SimpleCommander(BasicNavigator):
    """USB-waypoint Nav2 simple commander with watchdog recovery."""

    def __init__(self) -> None:
        super().__init__(node_name='simple_commander')

        self._declare_parameters()
        self._load_parameters()

        self.waypoint_file = self._resolve_waypoint_file(self.waypoint_file)
        self._waypoints: List[CraicWaypoint] = load_craic_waypoints(
            file_path=self.waypoint_file,
            coordinate_mode=self.coordinate_mode,
            origin_longitude_deg=self.map_origin_longitude_deg,
            origin_latitude_deg=self.map_origin_latitude_deg,
            map_origin_yaw_rad=self.map_origin_yaw_rad,
            map_origin_x_m=self.map_origin_x_m,
            map_origin_y_m=self.map_origin_y_m,
            use_first_waypoint_as_origin=self.use_first_waypoint_as_origin,
        )
        self.poses_list = [self._to_pose_stamped(waypoint) for waypoint in self._waypoints]

        self._cmd_vel_pub = self.create_publisher(Twist, self.cmd_vel_topic, 10)
        self._odom_sub = self.create_subscription(
            Odometry,
            self.pose_tracking_topic,
            self._on_pose_update,
            20,
        )

        self._current_pose_xy: Optional[tuple[float, float]] = None
        self._current_abs_waypoint_index = 0
        self._active_slice_start = 0
        self._last_logged_waypoint_index = -1
        self._last_progress_pose_xy: Optional[tuple[float, float]] = None
        self._last_progress_time = time.monotonic()
        self._recovery_attempts = 0

        self._log_loaded_route()

    def _declare_parameters(self) -> None:
        self.declare_parameter(
            'waypoint_file',
            '',
            ParameterDescriptor(
                description='Absolute path to waypoint.txt. Leave empty to auto-discover it on a USB drive.'
            ),
        )
        self.declare_parameter(
            'coordinate_mode',
            'auto',
            ParameterDescriptor(description='One of geodetic, cartesian_m, cartesian_cm, auto.'),
        )
        self.declare_parameter('map_origin_longitude_deg', 0.0)
        self.declare_parameter('map_origin_latitude_deg', 0.0)
        self.declare_parameter('map_origin_x_m', 0.0)
        self.declare_parameter('map_origin_y_m', 0.0)
        self.declare_parameter('map_origin_yaw_rad', 0.0)
        self.declare_parameter('use_first_waypoint_as_origin', True)
        self.declare_parameter('waypoint_frame_id', 'map')
        self.declare_parameter('pose_tracking_topic', '/odometry/global')
        self.declare_parameter('cmd_vel_topic', '/cmd_vel')
        self.declare_parameter('final_goal_stop_distance_m', 10.0)
        self.declare_parameter('stuck_timeout_sec', 10.0)
        self.declare_parameter('stuck_progress_radius_m', 0.8)
        self.declare_parameter('max_recovery_attempts', 6)
        self.declare_parameter('backup_distance_m', 0.8)
        self.declare_parameter('backup_speed_mps', 0.2)
        self.declare_parameter('spin_angle_rad', 2.0 * math.pi)
        self.declare_parameter('recovery_time_allowance_sec', 15.0)
        self.declare_parameter('progress_check_period_sec', 0.2)

    def _load_parameters(self) -> None:
        self.waypoint_file = self.get_parameter('waypoint_file').value
        self.coordinate_mode = self.get_parameter('coordinate_mode').value
        self.map_origin_longitude_deg = float(self.get_parameter('map_origin_longitude_deg').value)
        self.map_origin_latitude_deg = float(self.get_parameter('map_origin_latitude_deg').value)
        self.map_origin_x_m = float(self.get_parameter('map_origin_x_m').value)
        self.map_origin_y_m = float(self.get_parameter('map_origin_y_m').value)
        self.map_origin_yaw_rad = float(self.get_parameter('map_origin_yaw_rad').value)
        self.use_first_waypoint_as_origin = bool(
            self.get_parameter('use_first_waypoint_as_origin').value
        )
        self.waypoint_frame_id = self.get_parameter('waypoint_frame_id').value
        self.pose_tracking_topic = self.get_parameter('pose_tracking_topic').value
        self.cmd_vel_topic = self.get_parameter('cmd_vel_topic').value
        self.final_goal_stop_distance_m = float(
            self.get_parameter('final_goal_stop_distance_m').value
        )
        self.stuck_timeout_sec = float(self.get_parameter('stuck_timeout_sec').value)
        self.stuck_progress_radius_m = float(
            self.get_parameter('stuck_progress_radius_m').value
        )
        self.max_recovery_attempts = int(self.get_parameter('max_recovery_attempts').value)
        self.backup_distance_m = float(self.get_parameter('backup_distance_m').value)
        self.backup_speed_mps = float(self.get_parameter('backup_speed_mps').value)
        self.spin_angle_rad = float(self.get_parameter('spin_angle_rad').value)
        self.recovery_time_allowance_sec = float(
            self.get_parameter('recovery_time_allowance_sec').value
        )
        self.progress_check_period_sec = float(
            self.get_parameter('progress_check_period_sec').value
        )

    def _resolve_waypoint_file(self, configured_path: str) -> str:
        if configured_path:
            path = Path(configured_path).expanduser()
            if path.is_file():
                return str(path)
            raise FileNotFoundError(f'Configured waypoint_file does not exist: {path}')

        candidates = []
        cwd_candidate = Path.cwd() / 'waypoint.txt'
        candidates.append(cwd_candidate)

        if sys.platform.startswith('win'):
            for drive_letter in string.ascii_uppercase:
                candidates.append(Path(f'{drive_letter}:/waypoint.txt'))
        else:
            search_patterns = (
                '/media/*/*/waypoint.txt',
                '/media/*/waypoint.txt',
                '/mnt/*/waypoint.txt',
                '/mnt/waypoint.txt',
                '/run/media/*/*/waypoint.txt',
            )
            for pattern in search_patterns:
                candidates.extend(Path(path_str) for path_str in glob(pattern))

        for candidate in candidates:
            if candidate.is_file():
                self.get_logger().info(f'Auto-discovered USB waypoint file: {candidate}')
                return str(candidate)

        searched = ', '.join(str(candidate) for candidate in candidates[:8])
        raise FileNotFoundError(
            'Unable to find waypoint.txt. '
            'Set the waypoint_file parameter explicitly or mount the USB drive first. '
            f'Searched examples: {searched}'
        )

    def _on_pose_update(self, msg: Odometry) -> None:
        position = msg.pose.pose.position
        self._current_pose_xy = (position.x, position.y)

    def _to_pose_stamped(self, waypoint: CraicWaypoint) -> PoseStamped:
        pose = PoseStamped()
        pose.header.frame_id = self.waypoint_frame_id
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.pose.position.x = waypoint.x
        pose.pose.position.y = waypoint.y
        pose.pose.position.z = 0.0
        pose.pose.orientation.x = 0.0
        pose.pose.orientation.y = 0.0
        pose.pose.orientation.z = math.sin(waypoint.yaw * 0.5)
        pose.pose.orientation.w = math.cos(waypoint.yaw * 0.5)
        return pose

    def _log_loaded_route(self) -> None:
        self.get_logger().info(
            f'Loaded {len(self._waypoints)} waypoint(s) from {self.waypoint_file}'
        )
        preview_count = min(3, len(self._waypoints))
        for index in range(preview_count):
            waypoint = self._waypoints[index]
            self.get_logger().info(
                'poses_list['
                f'{index}] => x={waypoint.x:.2f}, y={waypoint.y:.2f}, yaw={waypoint.yaw:.3f}, '
                f'source=({waypoint.source_a:.8f}, {waypoint.source_b:.8f})'
            )

    def _log_current_waypoint(self, waypoint_index: int) -> None:
        if waypoint_index == self._last_logged_waypoint_index:
            return
        waypoint = self._waypoints[waypoint_index]
        self.get_logger().info(
            'Cruising to waypoint '
            f'{waypoint_index + 1}/{len(self._waypoints)} '
            f'(task_index={waypoint.index}, action={waypoint.action_label}, '
            f'x={waypoint.x:.2f}, y={waypoint.y:.2f})'
        )
        self._last_logged_waypoint_index = waypoint_index

    def _publish_zero_velocity(self, repeat_count: int = 5) -> None:
        stop_msg = Twist()
        for _ in range(repeat_count):
            self._cmd_vel_pub.publish(stop_msg)
            rclpy.spin_once(self, timeout_sec=0.05)

    def _wait_for_bt_navigator(self) -> None:
        self.get_logger().info('Waiting for bt_navigator to become active...')
        self._waitForNodeToActivate('bt_navigator')

    def _send_remaining_waypoints(self, start_index: int) -> bool:
        if start_index >= len(self.poses_list):
            return False

        self._active_slice_start = start_index
        self._current_abs_waypoint_index = start_index
        accepted = self.followWaypoints(self.poses_list[start_index:])
        if accepted:
            self._last_progress_time = time.monotonic()
            self._last_progress_pose_xy = self._current_pose_xy
            self._log_current_waypoint(start_index)
        return accepted

    def _wait_for_task_exit(self, timeout_sec: float) -> None:
        deadline = time.monotonic() + timeout_sec
        while time.monotonic() < deadline and not self.isTaskComplete():
            rclpy.spin_once(self, timeout_sec=0.1)

    def _run_spin_recovery(self) -> bool:
        if self.spin_angle_rad <= 0.0:
            return False
        self.get_logger().info(
            f'Running spin recovery for {self.spin_angle_rad:.2f} rad.'
        )
        accepted = self.spin(
            spin_dist=self.spin_angle_rad,
            time_allowance=self.recovery_time_allowance_sec,
        )
        if accepted:
            self._wait_for_task_exit(self.recovery_time_allowance_sec)
        return accepted

    def _run_backup_recovery(self) -> bool:
        if self.backup_distance_m <= 0.0:
            return False
        self.get_logger().info(
            f'Running backup recovery for {self.backup_distance_m:.2f} m.'
        )
        accepted = self.backup(
            backup_dist=self.backup_distance_m,
            backup_speed=self.backup_speed_mps,
            time_allowance=self.recovery_time_allowance_sec,
        )
        if accepted:
            self._wait_for_task_exit(self.recovery_time_allowance_sec)
        return accepted

    def _run_recovery_behavior(self) -> bool:
        if self._recovery_attempts >= self.max_recovery_attempts:
            self.get_logger().error('Reached max recovery attempts; aborting mission.')
            return False

        self._recovery_attempts += 1
        self.get_logger().warn(
            'DWA progress watchdog triggered after '
            f'{self.stuck_timeout_sec:.1f} s; running recovery attempt #{self._recovery_attempts}.'
        )

        self.cancelTask()
        self._wait_for_task_exit(timeout_sec=3.0)
        self._publish_zero_velocity()

        prefer_spin = self._recovery_attempts % 2 == 1
        recovery_ok = False
        if prefer_spin:
            recovery_ok = self._run_spin_recovery() or self._run_backup_recovery()
        else:
            recovery_ok = self._run_backup_recovery() or self._run_spin_recovery()

        try:
            self.clearAllCostmaps()
        except Exception as exc:  # pragma: no cover - depends on Nav2 runtime
            self.get_logger().warn(f'Costmap clear skipped: {exc}')

        if not recovery_ok:
            self.get_logger().error('Recovery behavior was rejected by Nav2.')
            return False

        return self._send_remaining_waypoints(self._current_abs_waypoint_index)

    def _should_trigger_final_stop(self) -> bool:
        if self._current_pose_xy is None or not self._waypoints:
            return False

        final_waypoint = self._waypoints[-1]
        return (
            distance_xy(
                self._current_pose_xy[0],
                self._current_pose_xy[1],
                final_waypoint.x,
                final_waypoint.y,
            )
            <= self.final_goal_stop_distance_m
        )

    def _update_feedback_state(self) -> None:
        feedback = self.getFeedback()
        if feedback is None:
            return

        relative_index = int(feedback.current_waypoint)
        absolute_index = min(
            self._active_slice_start + relative_index,
            len(self._waypoints) - 1,
        )
        self._current_abs_waypoint_index = absolute_index
        self._log_current_waypoint(absolute_index)

    def _update_progress_watchdog(self) -> bool:
        if self._current_pose_xy is None:
            return False

        if self._last_progress_pose_xy is None:
            self._last_progress_pose_xy = self._current_pose_xy
            self._last_progress_time = time.monotonic()
            return False

        moved = distance_xy(
            self._last_progress_pose_xy[0],
            self._last_progress_pose_xy[1],
            self._current_pose_xy[0],
            self._current_pose_xy[1],
        )
        if moved >= self.stuck_progress_radius_m:
            self._last_progress_pose_xy = self._current_pose_xy
            self._last_progress_time = time.monotonic()
            return False

        return (time.monotonic() - self._last_progress_time) >= self.stuck_timeout_sec

    def run(self) -> int:
        self._wait_for_bt_navigator()

        if not self._send_remaining_waypoints(0):
            self.get_logger().error('Nav2 rejected the initial waypoint mission.')
            return 1

        while rclpy.ok():
            rclpy.spin_once(self, timeout_sec=self.progress_check_period_sec)
            self._update_feedback_state()

            if self._should_trigger_final_stop():
                self.get_logger().info(
                    f'Within {self.final_goal_stop_distance_m:.2f} m of the final goal; forcing stop.'
                )
                self.cancelTask()
                self._wait_for_task_exit(timeout_sec=2.0)
                self._publish_zero_velocity()
                return 0

            if self.isTaskComplete():
                result = self.getResult()
                self._publish_zero_velocity()
                if result == TaskResult.SUCCEEDED:
                    self.get_logger().info('Simple commander mission completed successfully.')
                    return 0
                if result == TaskResult.CANCELED:
                    self.get_logger().warn('Simple commander mission canceled.')
                    return 1
                self.get_logger().error(f'Simple commander mission failed with result: {result}')
                return 1

            if self._update_progress_watchdog():
                if not self._run_recovery_behavior():
                    self._publish_zero_velocity()
                    return 1

        self._publish_zero_velocity()
        return 1


def main() -> None:
    rclpy.init()
    navigator: Optional[SimpleCommander] = None
    exit_code = 1

    try:
        navigator = SimpleCommander()
        exit_code = navigator.run()
    except Exception as exc:
        if navigator is not None:
            navigator.get_logger().fatal(f'Simple commander crashed: {exc}')
        else:
            print(f'Simple commander crashed before node startup: {exc}', file=sys.stderr)
        exit_code = 1
    finally:
        if navigator is not None:
            navigator.destroy_node()
        rclpy.shutdown()
        sys.exit(exit_code)


if __name__ == '__main__':
    main()
