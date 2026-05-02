"""Semantic obstacle tracking and decision helpers for CRAIC navigation.

This module adds a thin semantic layer above Nav2:
- detect the closest obstacle in the frontal lane corridor from LaserScan
- estimate obstacle longitudinal speed with an alpha-beta tracker
- classify the situation into follow / overtake / left-bypass / return
- synthesize short temporary waypoint maneuvers for semantic passing

It intentionally stays lightweight and ROS-message agnostic so it can be
embedded into the existing waypoint mission node without introducing a new
message package.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import time
from typing import List, Optional, Sequence, Tuple

from geometry_msgs.msg import PoseStamped
from sensor_msgs.msg import LaserScan


def normalize_angle(angle: float) -> float:
    """Wrap ``angle`` to [-pi, pi]."""
    return math.atan2(math.sin(angle), math.cos(angle))


@dataclass
class Pose2D:
    """Small utility pose used by semantic planning helpers."""

    x: float
    y: float
    yaw: float


@dataclass
class TrackedObstacle:
    """Tracked frontal obstacle state in the robot body frame."""

    stamp_sec: float
    x_m: float
    y_m: float
    distance_m: float
    lateral_clearance_left_m: float
    lateral_clearance_right_m: float
    relative_speed_mps: float
    obstacle_speed_mps: float


@dataclass
class SemanticDecision:
    """High-level semantic action emitted by the decision layer."""

    state: str
    reason: str
    obstacle: Optional[TrackedObstacle] = None


class AlphaBeta1DTracker:
    """Simple alpha-beta filter for one-dimensional range-rate tracking."""

    def __init__(self, alpha: float = 0.65, beta: float = 0.10) -> None:
        self.alpha = alpha
        self.beta = beta
        self._x: Optional[float] = None
        self._v = 0.0
        self._stamp_sec: Optional[float] = None

    def reset(self) -> None:
        self._x = None
        self._v = 0.0
        self._stamp_sec = None

    def update(self, measurement_x_m: float, stamp_sec: float) -> tuple[float, float]:
        if self._x is None or self._stamp_sec is None:
            self._x = measurement_x_m
            self._stamp_sec = stamp_sec
            self._v = 0.0
            return self._x, self._v

        dt = max(1e-3, stamp_sec - self._stamp_sec)
        x_pred = self._x + self._v * dt
        residual = measurement_x_m - x_pred

        self._x = x_pred + self.alpha * residual
        self._v = self._v + (self.beta / dt) * residual
        self._stamp_sec = stamp_sec
        return self._x, self._v


class SemanticObstacleBehavior:
    """Semantic obstacle detector, tracker, and decision maker."""

    def __init__(
        self,
        *,
        lane_half_width_m: float = 1.2,
        frontal_detection_distance_m: float = 12.0,
        left_clearance_window_m: float = 2.5,
        obstacle_timeout_sec: float = 0.8,
        slow_vehicle_speed_threshold_mps: float = 1.5,
        fast_vehicle_speed_threshold_mps: float = 3.5,
        overtake_trigger_distance_m: float = 8.0,
        follow_trigger_distance_m: float = 10.0,
        desired_follow_distance_m: float = 4.5,
        overtake_lateral_offset_m: float = 1.4,
        bypass_lateral_offset_m: float = 0.85,
        overtake_pass_margin_m: float = 2.0,
        return_to_lane_margin_m: float = 3.0,
        maneuver_cooldown_sec: float = 5.0,
    ) -> None:
        self.lane_half_width_m = lane_half_width_m
        self.frontal_detection_distance_m = frontal_detection_distance_m
        self.left_clearance_window_m = left_clearance_window_m
        self.obstacle_timeout_sec = obstacle_timeout_sec
        self.slow_vehicle_speed_threshold_mps = slow_vehicle_speed_threshold_mps
        self.fast_vehicle_speed_threshold_mps = fast_vehicle_speed_threshold_mps
        self.overtake_trigger_distance_m = overtake_trigger_distance_m
        self.follow_trigger_distance_m = follow_trigger_distance_m
        self.desired_follow_distance_m = desired_follow_distance_m
        self.overtake_lateral_offset_m = overtake_lateral_offset_m
        self.bypass_lateral_offset_m = bypass_lateral_offset_m
        self.overtake_pass_margin_m = overtake_pass_margin_m
        self.return_to_lane_margin_m = return_to_lane_margin_m
        self.maneuver_cooldown_sec = maneuver_cooldown_sec

        self._tracker = AlphaBeta1DTracker()
        self._latest_obstacle: Optional[TrackedObstacle] = None
        self._last_decision_state = 'CRUISE'
        self._last_maneuver_time_sec = 0.0

    def _cluster_frontal_points(
        self, points: Sequence[tuple[float, float]]
    ) -> list[list[tuple[float, float]]]:
        if not points:
            return []

        clusters: list[list[tuple[float, float]]] = []
        current = [points[0]]

        for point in points[1:]:
            prev = current[-1]
            if math.hypot(point[0] - prev[0], point[1] - prev[1]) <= 0.45:
                current.append(point)
            else:
                clusters.append(current)
                current = [point]

        clusters.append(current)
        return clusters

    def _extract_front_obstacle(
        self,
        scan: LaserScan,
        robot_speed_mps: float,
    ) -> Optional[TrackedObstacle]:
        body_points: list[tuple[float, float]] = []
        left_points: list[tuple[float, float]] = []
        right_points: list[tuple[float, float]] = []

        angle = scan.angle_min
        stamp_sec = time.monotonic()

        for range_value in scan.ranges:
            if math.isfinite(range_value) and scan.range_min < range_value < min(
                scan.range_max, self.frontal_detection_distance_m
            ):
                x_value = range_value * math.cos(angle)
                y_value = range_value * math.sin(angle)

                if 0.2 < x_value < self.frontal_detection_distance_m:
                    if abs(y_value) <= self.lane_half_width_m:
                        body_points.append((x_value, y_value))
                    if 0.0 < y_value < self.left_clearance_window_m:
                        left_points.append((x_value, y_value))
                    if -self.left_clearance_window_m < y_value < 0.0:
                        right_points.append((x_value, y_value))
            angle += scan.angle_increment

        if not body_points:
            self._latest_obstacle = None
            self._tracker.reset()
            return None

        body_points.sort(key=lambda point: math.atan2(point[1], point[0]))
        clusters = self._cluster_frontal_points(body_points)
        best_cluster = min(clusters, key=lambda cluster: min(point[0] for point in cluster))

        centroid_x = sum(point[0] for point in best_cluster) / len(best_cluster)
        centroid_y = sum(point[1] for point in best_cluster) / len(best_cluster)
        nearest_x = min(point[0] for point in best_cluster)
        measured_distance = math.hypot(centroid_x, centroid_y)

        filtered_x, relative_speed = self._tracker.update(nearest_x, stamp_sec)
        obstacle_speed = max(0.0, robot_speed_mps + relative_speed)

        left_clearance = min((point[1] for point in left_points), default=self.left_clearance_window_m)
        right_clearance = abs(
            max((point[1] for point in right_points), default=-self.left_clearance_window_m)
        )

        obstacle = TrackedObstacle(
            stamp_sec=stamp_sec,
            x_m=filtered_x,
            y_m=centroid_y,
            distance_m=measured_distance,
            lateral_clearance_left_m=max(0.0, left_clearance - abs(centroid_y)),
            lateral_clearance_right_m=max(0.0, right_clearance - abs(centroid_y)),
            relative_speed_mps=relative_speed,
            obstacle_speed_mps=obstacle_speed,
        )
        self._latest_obstacle = obstacle
        return obstacle

    def update_from_scan(
        self,
        scan: LaserScan,
        *,
        robot_speed_mps: float,
        waypoint_action_label: str,
    ) -> SemanticDecision:
        obstacle = self._extract_front_obstacle(scan, robot_speed_mps=robot_speed_mps)
        if obstacle is None:
            self._last_decision_state = 'CRUISE'
            return SemanticDecision(state='CRUISE', reason='no_front_obstacle')

        now_sec = time.monotonic()
        if now_sec - self._last_maneuver_time_sec < self.maneuver_cooldown_sec:
            return SemanticDecision(state='CRUISE', reason='maneuver_cooldown', obstacle=obstacle)

        supports_left_maneuver = waypoint_action_label in {
            'unknown',
            'straight',
            'lane_change_left',
            'overtake',
        }
        left_open_for_overtake = obstacle.lateral_clearance_left_m >= self.overtake_lateral_offset_m
        left_open_for_bypass = obstacle.lateral_clearance_left_m >= self.bypass_lateral_offset_m

        if (
            obstacle.distance_m <= self.follow_trigger_distance_m
            and obstacle.obstacle_speed_mps >= self.fast_vehicle_speed_threshold_mps
        ):
            self._last_decision_state = 'FOLLOW_FAST'
            return SemanticDecision(
                state='FOLLOW_FAST',
                reason='fast_front_vehicle',
                obstacle=obstacle,
            )

        if (
            supports_left_maneuver
            and obstacle.distance_m <= self.overtake_trigger_distance_m
            and obstacle.obstacle_speed_mps <= self.slow_vehicle_speed_threshold_mps
            and left_open_for_overtake
        ):
            self._last_decision_state = 'OVERTAKE_LEFT'
            return SemanticDecision(
                state='OVERTAKE_LEFT',
                reason='slow_front_vehicle_with_left_clearance',
                obstacle=obstacle,
            )

        if (
            supports_left_maneuver
            and obstacle.distance_m <= self.overtake_trigger_distance_m
            and left_open_for_bypass
        ):
            self._last_decision_state = 'BYPASS_LEFT'
            return SemanticDecision(
                state='BYPASS_LEFT',
                reason='single_lane_left_bypass',
                obstacle=obstacle,
            )

        self._last_decision_state = 'CRUISE'
        return SemanticDecision(
            state='CRUISE',
            reason='front_obstacle_but_no_semantic_override',
            obstacle=obstacle,
        )

    def note_maneuver_started(self) -> None:
        self._last_maneuver_time_sec = time.monotonic()

    def should_keep_following(self) -> bool:
        obstacle = self._latest_obstacle
        if obstacle is None:
            return False
        age_sec = time.monotonic() - obstacle.stamp_sec
        return (
            age_sec <= self.obstacle_timeout_sec
            and obstacle.distance_m <= self.follow_trigger_distance_m + 2.0
        )

    def build_follow_command(
        self,
        *,
        max_follow_speed_mps: float,
        heading_gain: float = 1.2,
        gap_gain: float = 0.55,
    ) -> tuple[float, float]:
        obstacle = self._latest_obstacle
        if obstacle is None:
            return 0.0, 0.0

        gap_error = obstacle.x_m - self.desired_follow_distance_m
        target_speed = max(
            0.0,
            min(max_follow_speed_mps, obstacle.obstacle_speed_mps + gap_gain * gap_error),
        )
        target_yaw_rate = max(
            -0.8,
            min(0.8, heading_gain * math.atan2(obstacle.y_m, max(0.5, obstacle.x_m))),
        )
        return target_speed, target_yaw_rate

    def build_semantic_maneuver(
        self,
        *,
        current_pose: Pose2D,
        next_route_pose: Optional[Pose2D],
        mode: str,
    ) -> List[PoseStamped]:
        obstacle = self._latest_obstacle
        if obstacle is None:
            return []

        heading = current_pose.yaw
        if next_route_pose is not None:
            heading = math.atan2(
                next_route_pose.y - current_pose.y,
                next_route_pose.x - current_pose.x,
            )

        left_dx = -math.sin(heading)
        left_dy = math.cos(heading)
        forward_dx = math.cos(heading)
        forward_dy = math.sin(heading)

        if mode == 'OVERTAKE_LEFT':
            lateral_offset = min(
                self.overtake_lateral_offset_m,
                max(self.bypass_lateral_offset_m, obstacle.lateral_clearance_left_m * 0.9),
            )
        else:
            lateral_offset = min(
                self.bypass_lateral_offset_m,
                max(0.6, obstacle.lateral_clearance_left_m * 0.8),
            )

        pass_forward = obstacle.x_m + self.overtake_pass_margin_m
        return_forward = pass_forward + self.return_to_lane_margin_m

        maneuver_points = [
            Pose2D(
                x=current_pose.x + forward_dx * 1.5 + left_dx * lateral_offset,
                y=current_pose.y + forward_dy * 1.5 + left_dy * lateral_offset,
                yaw=heading,
            ),
            Pose2D(
                x=current_pose.x + forward_dx * pass_forward + left_dx * lateral_offset,
                y=current_pose.y + forward_dy * pass_forward + left_dy * lateral_offset,
                yaw=heading,
            ),
            Pose2D(
                x=current_pose.x + forward_dx * return_forward,
                y=current_pose.y + forward_dy * return_forward,
                yaw=heading,
            ),
        ]

        result: list[PoseStamped] = []
        for pose_2d in maneuver_points:
            pose = PoseStamped()
            pose.header.frame_id = 'map'
            pose.pose.position.x = pose_2d.x
            pose.pose.position.y = pose_2d.y
            pose.pose.position.z = 0.0
            pose.pose.orientation.x = 0.0
            pose.pose.orientation.y = 0.0
            pose.pose.orientation.z = math.sin(pose_2d.yaw * 0.5)
            pose.pose.orientation.w = math.cos(pose_2d.yaw * 0.5)
            result.append(pose)

        return result
