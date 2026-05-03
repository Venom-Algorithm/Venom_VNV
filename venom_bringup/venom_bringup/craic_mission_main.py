"""CRAIC competition mission commander built on Nav2 Simple Commander."""

from __future__ import annotations

import math
import sys
import time
from typing import List, Optional

import rclpy
from geometry_msgs.msg import PoseStamped, Twist
from nav_msgs.msg import Odometry
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from rcl_interfaces.msg import ParameterDescriptor
from sensor_msgs.msg import LaserScan

from venom_bringup.craic_waypoint_utils import CraicWaypoint, load_craic_waypoints
from venom_bringup.semantic_obstacle_behavior import (
    Pose2D,
    SemanticDecision,
    SemanticObstacleBehavior,
)


def distance_xy(x1: float, y1: float, x2: float, y2: float) -> float:
    return math.hypot(x2 - x1, y2 - y1)


class CraicMissionCommander(BasicNavigator):
    """Waypoint-driven competition mission node."""

    def __init__(self) -> None:
        super().__init__(node_name='craic_mission_main')

        self._declare_parameters()
        self._load_parameters()

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
        self._goal_poses = [self._to_pose_stamped(waypoint) for waypoint in self._waypoints]

        self._cmd_vel_pub = self.create_publisher(Twist, self.cmd_vel_topic, 10)
        self._odom_sub = self.create_subscription(
            Odometry,
            self.pose_tracking_topic,
            self._on_pose_update,
            20,
        )
        self._scan_sub = self.create_subscription(
            LaserScan,
            self.scan_topic,
            self._on_scan_update,
            20,
        )

        self._current_pose_xy: Optional[tuple[float, float]] = None
        self._current_pose_yaw: Optional[float] = None
        self._current_linear_speed_mps = 0.0
        self._current_abs_waypoint_index = 0
        self._active_slice_start = 0
        self._last_logged_waypoint_index = -1
        self._last_progress_pose_xy: Optional[tuple[float, float]] = None
        self._last_progress_time = time.monotonic()
        self._recovery_attempts = 0
        self._latest_semantic_decision = SemanticDecision(
            state='CRUISE',
            reason='startup',
        )
        self._last_semantic_log_state = ''
        self._semantic_behavior: Optional[SemanticObstacleBehavior] = None
        if self.enable_semantic_obstacle_logic:
            self._semantic_behavior = SemanticObstacleBehavior(
                lane_half_width_m=self.semantic_lane_half_width_m,
                frontal_detection_distance_m=self.semantic_frontal_detection_distance_m,
                left_clearance_window_m=self.semantic_left_clearance_window_m,
                obstacle_timeout_sec=self.semantic_obstacle_timeout_sec,
                slow_vehicle_speed_threshold_mps=self.semantic_slow_vehicle_speed_threshold_mps,
                fast_vehicle_speed_threshold_mps=self.semantic_fast_vehicle_speed_threshold_mps,
                overtake_trigger_distance_m=self.semantic_overtake_trigger_distance_m,
                follow_trigger_distance_m=self.semantic_follow_trigger_distance_m,
                desired_follow_distance_m=self.semantic_desired_follow_distance_m,
                overtake_lateral_offset_m=self.semantic_overtake_lateral_offset_m,
                bypass_lateral_offset_m=self.semantic_bypass_lateral_offset_m,
                overtake_pass_margin_m=self.semantic_overtake_pass_margin_m,
                return_to_lane_margin_m=self.semantic_return_to_lane_margin_m,
                maneuver_cooldown_sec=self.semantic_maneuver_cooldown_sec,
            )

    def _declare_parameters(self) -> None:
        self.declare_parameter(
            'waypoint_file',
            '',
            ParameterDescriptor(description='Path to CRAIC waypoint.txt task file.'),
        )
        self.declare_parameter(
            'coordinate_mode',
            'geodetic',
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
        self.declare_parameter('scan_topic', '/scan')
        self.declare_parameter('final_goal_stop_distance_m', 10.0)
        self.declare_parameter('stuck_timeout_sec', 10.0)
        self.declare_parameter('stuck_progress_radius_m', 0.8)
        self.declare_parameter('max_recovery_attempts', 5)
        self.declare_parameter('backup_distance_m', 0.8)
        self.declare_parameter('backup_speed_mps', 0.2)
        self.declare_parameter('spin_angle_rad', 1.57)
        self.declare_parameter('recovery_time_allowance_sec', 15.0)
        self.declare_parameter('progress_check_period_sec', 0.2)
        self.declare_parameter('enable_semantic_obstacle_logic', True)
        self.declare_parameter('semantic_lane_half_width_m', 1.2)
        self.declare_parameter('semantic_frontal_detection_distance_m', 12.0)
        self.declare_parameter('semantic_left_clearance_window_m', 2.5)
        self.declare_parameter('semantic_obstacle_timeout_sec', 0.8)
        self.declare_parameter('semantic_slow_vehicle_speed_threshold_mps', 1.5)
        self.declare_parameter('semantic_fast_vehicle_speed_threshold_mps', 3.5)
        self.declare_parameter('semantic_overtake_trigger_distance_m', 8.0)
        self.declare_parameter('semantic_follow_trigger_distance_m', 10.0)
        self.declare_parameter('semantic_desired_follow_distance_m', 4.5)
        self.declare_parameter('semantic_overtake_lateral_offset_m', 1.4)
        self.declare_parameter('semantic_bypass_lateral_offset_m', 0.85)
        self.declare_parameter('semantic_overtake_pass_margin_m', 2.0)
        self.declare_parameter('semantic_return_to_lane_margin_m', 3.0)
        self.declare_parameter('semantic_maneuver_cooldown_sec', 5.0)
        self.declare_parameter('semantic_max_follow_speed_mps', 3.0)
        self.declare_parameter('semantic_follow_behavior_timeout_sec', 8.0)

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
        self.scan_topic = self.get_parameter('scan_topic').value
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
        self.enable_semantic_obstacle_logic = bool(
            self.get_parameter('enable_semantic_obstacle_logic').value
        )
        self.semantic_lane_half_width_m = float(
            self.get_parameter('semantic_lane_half_width_m').value
        )
        self.semantic_frontal_detection_distance_m = float(
            self.get_parameter('semantic_frontal_detection_distance_m').value
        )
        self.semantic_left_clearance_window_m = float(
            self.get_parameter('semantic_left_clearance_window_m').value
        )
        self.semantic_obstacle_timeout_sec = float(
            self.get_parameter('semantic_obstacle_timeout_sec').value
        )
        self.semantic_slow_vehicle_speed_threshold_mps = float(
            self.get_parameter('semantic_slow_vehicle_speed_threshold_mps').value
        )
        self.semantic_fast_vehicle_speed_threshold_mps = float(
            self.get_parameter('semantic_fast_vehicle_speed_threshold_mps').value
        )
        self.semantic_overtake_trigger_distance_m = float(
            self.get_parameter('semantic_overtake_trigger_distance_m').value
        )
        self.semantic_follow_trigger_distance_m = float(
            self.get_parameter('semantic_follow_trigger_distance_m').value
        )
        self.semantic_desired_follow_distance_m = float(
            self.get_parameter('semantic_desired_follow_distance_m').value
        )
        self.semantic_overtake_lateral_offset_m = float(
            self.get_parameter('semantic_overtake_lateral_offset_m').value
        )
        self.semantic_bypass_lateral_offset_m = float(
            self.get_parameter('semantic_bypass_lateral_offset_m').value
        )
        self.semantic_overtake_pass_margin_m = float(
            self.get_parameter('semantic_overtake_pass_margin_m').value
        )
        self.semantic_return_to_lane_margin_m = float(
            self.get_parameter('semantic_return_to_lane_margin_m').value
        )
        self.semantic_maneuver_cooldown_sec = float(
            self.get_parameter('semantic_maneuver_cooldown_sec').value
        )
        self.semantic_max_follow_speed_mps = float(
            self.get_parameter('semantic_max_follow_speed_mps').value
        )
        self.semantic_follow_behavior_timeout_sec = float(
            self.get_parameter('semantic_follow_behavior_timeout_sec').value
        )

    def _on_pose_update(self, msg: Odometry) -> None:
        position = msg.pose.pose.position
        self._current_pose_xy = (position.x, position.y)
        orientation = msg.pose.pose.orientation
        self._current_pose_yaw = math.atan2(
            2.0 * (orientation.w * orientation.z + orientation.x * orientation.y),
            1.0 - 2.0 * (orientation.y * orientation.y + orientation.z * orientation.z),
        )
        self._current_linear_speed_mps = float(msg.twist.twist.linear.x)

    def _on_scan_update(self, msg: LaserScan) -> None:
        if self._semantic_behavior is None:
            return

        current_action_label = 'straight'
        if 0 <= self._current_abs_waypoint_index < len(self._waypoints):
            current_action_label = self._waypoints[self._current_abs_waypoint_index].action_label

        self._latest_semantic_decision = self._semantic_behavior.update_from_scan(
            msg,
            robot_speed_mps=max(0.0, self._current_linear_speed_mps),
            waypoint_action_label=current_action_label,
        )

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

    def _log_current_waypoint(self, waypoint_index: int) -> None:
        if waypoint_index == self._last_logged_waypoint_index:
            return
        waypoint = self._waypoints[waypoint_index]
        self.get_logger().info(
            'Heading to waypoint '
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
        if start_index >= len(self._goal_poses):
            return False

        self._active_slice_start = start_index
        self._current_abs_waypoint_index = start_index
        accepted = self.followWaypoints(self._goal_poses[start_index:])
        if accepted:
            self._last_progress_time = time.monotonic()
            self._last_progress_pose_xy = self._current_pose_xy
            self._log_current_waypoint(start_index)
        return accepted

    def _wait_for_task_exit(self, timeout_sec: float) -> None:
        deadline = time.monotonic() + timeout_sec
        while time.monotonic() < deadline and not self.isTaskComplete():
            rclpy.spin_once(self, timeout_sec=0.1)

    def _get_current_pose_2d(self) -> Optional[Pose2D]:
        if self._current_pose_xy is None or self._current_pose_yaw is None:
            return None
        return Pose2D(
            x=self._current_pose_xy[0],
            y=self._current_pose_xy[1],
            yaw=self._current_pose_yaw,
        )

    def _get_next_route_pose_2d(self) -> Optional[Pose2D]:
        next_index = min(self._current_abs_waypoint_index + 1, len(self._waypoints) - 1)
        if next_index < 0 or next_index >= len(self._waypoints):
            return None
        waypoint = self._waypoints[next_index]
        return Pose2D(x=waypoint.x, y=waypoint.y, yaw=waypoint.yaw)

    def _log_semantic_decision(self) -> None:
        state = self._latest_semantic_decision.state
        if state == self._last_semantic_log_state:
            return
        obstacle = self._latest_semantic_decision.obstacle
        if obstacle is None:
            self.get_logger().info(
                f'Semantic obstacle state -> {state} ({self._latest_semantic_decision.reason})'
            )
        else:
            self.get_logger().info(
                'Semantic obstacle state -> '
                f'{state} ({self._latest_semantic_decision.reason}), '
                f'd={obstacle.distance_m:.2f} m, '
                f'obs_v={obstacle.obstacle_speed_mps:.2f} m/s, '
                f'left_clear={obstacle.lateral_clearance_left_m:.2f} m'
            )
        self._last_semantic_log_state = state

    def _run_follow_behavior(self) -> bool:
        if self._semantic_behavior is None:
            return False

        self.get_logger().info('Semantic decision: follow fast front vehicle.')
        self._semantic_behavior.note_maneuver_started()
        self.cancelTask()
        self._wait_for_task_exit(timeout_sec=2.0)

        deadline = time.monotonic() + self.semantic_follow_behavior_timeout_sec
        while rclpy.ok() and time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.1)
            if not self._semantic_behavior.should_keep_following():
                break

            follow_speed, yaw_rate = self._semantic_behavior.build_follow_command(
                max_follow_speed_mps=self.semantic_max_follow_speed_mps
            )
            cmd = Twist()
            cmd.linear.x = follow_speed
            cmd.angular.z = yaw_rate
            self._cmd_vel_pub.publish(cmd)

        self._publish_zero_velocity()
        return self._send_remaining_waypoints(self._current_abs_waypoint_index)

    def _run_semantic_maneuver(self, mode: str) -> bool:
        if self._semantic_behavior is None:
            return False

        current_pose = self._get_current_pose_2d()
        if current_pose is None:
            return False

        maneuver_poses = self._semantic_behavior.build_semantic_maneuver(
            current_pose=current_pose,
            next_route_pose=self._get_next_route_pose_2d(),
            mode=mode,
        )
        if not maneuver_poses:
            return False

        self.get_logger().warn(f'Semantic decision: {mode}, injecting temporary maneuver poses.')
        self._semantic_behavior.note_maneuver_started()
        self.cancelTask()
        self._wait_for_task_exit(timeout_sec=2.0)
        self._publish_zero_velocity()

        accepted = self.followWaypoints(maneuver_poses)
        if not accepted:
            self.get_logger().error('Semantic maneuver was rejected by Nav2.')
            return False

        while rclpy.ok() and not self.isTaskComplete():
            rclpy.spin_once(self, timeout_sec=0.1)

        result = self.getResult()
        self._publish_zero_velocity()
        if result != TaskResult.SUCCEEDED:
            self.get_logger().warn(f'Semantic maneuver ended with result: {result}')
            return False

        self.get_logger().info('Semantic maneuver complete, returning to main route.')
        return self._send_remaining_waypoints(self._current_abs_waypoint_index)

    def _run_recovery_behavior(self) -> bool:
        if self._recovery_attempts >= self.max_recovery_attempts:
            self.get_logger().error('Reached max recovery attempts; aborting mission.')
            return False

        self._recovery_attempts += 1
        self.get_logger().warn(
            f'Planner appears stuck; running recovery attempt #{self._recovery_attempts}.'
        )

        self.cancelTask()
        self._wait_for_task_exit(timeout_sec=3.0)
        self._publish_zero_velocity()

        if self.backup_distance_m > 0.0:
            self.get_logger().info(
                f'Backing up {self.backup_distance_m:.2f} m before retrying route.'
            )
            if self.backup(
                backup_dist=self.backup_distance_m,
                backup_speed=self.backup_speed_mps,
                time_allowance=self.recovery_time_allowance_sec,
            ):
                self._wait_for_task_exit(self.recovery_time_allowance_sec)

        if self.spin_angle_rad > 0.0:
            self.get_logger().info(
                f'Spinning {self.spin_angle_rad:.2f} rad to refresh obstacle observations.'
            )
            if self.spin(
                spin_dist=self.spin_angle_rad,
                time_allowance=self.recovery_time_allowance_sec,
            ):
                self._wait_for_task_exit(self.recovery_time_allowance_sec)

        try:
            self.clearAllCostmaps()
        except Exception as exc:  # pragma: no cover - depends on Nav2 runtime
            self.get_logger().warn(f'Costmap clear skipped: {exc}')

        return self._send_remaining_waypoints(self._current_abs_waypoint_index)

    def _should_trigger_final_stop(self) -> bool:
        if self._current_pose_xy is None or not self._goal_poses:
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
        self.get_logger().info(
            f'Loaded {len(self._waypoints)} CRAIC waypoint(s) from {self.waypoint_file}'
        )
        if self.enable_semantic_obstacle_logic:
            self.get_logger().info(
                'Semantic obstacle logic enabled: follow / overtake / left-bypass / return-to-lane.'
            )
        self._wait_for_bt_navigator()

        if not self._send_remaining_waypoints(0):
            self.get_logger().error('Nav2 rejected the initial waypoint mission.')
            return 1

        while rclpy.ok():
            rclpy.spin_once(self, timeout_sec=self.progress_check_period_sec)
            self._update_feedback_state()
            self._log_semantic_decision()

            if self._should_trigger_final_stop():
                self.get_logger().info(
                    f'Within {self.final_goal_stop_distance_m:.2f} m of final goal; forcing stop.'
                )
                self.cancelTask()
                self._wait_for_task_exit(timeout_sec=2.0)
                self._publish_zero_velocity()
                return 0

            if self.enable_semantic_obstacle_logic:
                if self._latest_semantic_decision.state == 'FOLLOW_FAST':
                    if not self._run_follow_behavior():
                        self._publish_zero_velocity()
                        return 1
                    continue

                if self._latest_semantic_decision.state == 'OVERTAKE_LEFT':
                    if not self._run_semantic_maneuver('OVERTAKE_LEFT'):
                        self.get_logger().warn(
                            'Semantic overtake failed; falling back to normal Nav2 recovery.'
                        )
                    continue

                if self._latest_semantic_decision.state == 'BYPASS_LEFT':
                    if not self._run_semantic_maneuver('BYPASS_LEFT'):
                        self.get_logger().warn(
                            'Semantic left-bypass failed; falling back to normal Nav2 recovery.'
                        )
                    continue

            if self.isTaskComplete():
                result = self.getResult()
                self._publish_zero_velocity()
                if result == TaskResult.SUCCEEDED:
                    self.get_logger().info('CRAIC mission completed successfully.')
                    return 0
                if result == TaskResult.CANCELED:
                    self.get_logger().warn('CRAIC mission canceled.')
                    return 1
                self.get_logger().error(f'CRAIC mission failed with result: {result}')
                return 1

            if self._update_progress_watchdog():
                if not self._run_recovery_behavior():
                    self._publish_zero_velocity()
                    return 1

        self._publish_zero_velocity()
        return 1


def main() -> None:
    rclpy.init()
    navigator: Optional[CraicMissionCommander] = None
    exit_code = 1

    try:
        navigator = CraicMissionCommander()
        exit_code = navigator.run()
    except Exception as exc:
        if navigator is not None:
            navigator.get_logger().fatal(f'CRAIC mission crashed: {exc}')
        else:
            print(f'CRAIC mission crashed before node startup: {exc}', file=sys.stderr)
        exit_code = 1
    finally:
        if navigator is not None:
            navigator.destroy_node()
        rclpy.shutdown()
        sys.exit(exit_code)


if __name__ == '__main__':
    main()
