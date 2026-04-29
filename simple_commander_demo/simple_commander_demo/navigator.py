import math
import time
from typing import Any

from geometry_msgs.msg import PoseStamped
from rclpy.parameter import Parameter

from simple_commander_demo.models import WaypointSpec


class MockWaypointNavigator:
    def __init__(self, node: Any, delay_sec: float = 0.5):
        self.node = node
        self.delay_sec = delay_sec

    def wait_until_ready(self) -> None:
        self.node.get_logger().info('Mock navigator is ready; no Nav2 server required.')

    def go_to_waypoint(self, waypoint: WaypointSpec) -> None:
        self.node.get_logger().info(
            f'[MOCK NAV] Going to {waypoint.name}: '
            f'x={waypoint.x:.2f}, y={waypoint.y:.2f}, yaw={waypoint.yaw:.3f}'
        )

    def wait_until_done(self) -> bool:
        time.sleep(max(self.delay_sec, 0.0))
        self.node.get_logger().info('[MOCK NAV] Navigation succeeded.')
        return True

    def cancel(self) -> None:
        self.node.get_logger().warn('[MOCK NAV] Cancel requested.')

    def shutdown(self) -> None:
        return None


class Nav2WaypointNavigator:
    def __init__(self, node: Any, wait_mode: str = 'bt_navigator', use_sim_time: bool = False):
        from nav2_simple_commander.robot_navigator import BasicNavigator

        self.node = node
        self.wait_mode = wait_mode
        self.navigator = BasicNavigator(node_name='simple_commander_nav2')
        self._configure_use_sim_time(use_sim_time)

    def wait_until_ready(self) -> None:
        self.node.get_logger().info(f'Waiting for Nav2 with mode: {self.wait_mode}')
        if self.wait_mode == 'full':
            self.navigator.waitUntilNav2Active()
            return

        if hasattr(self.navigator, '_waitForNodeToActivate'):
            self.navigator._waitForNodeToActivate('bt_navigator')
            return

        self.navigator.waitUntilNav2Active()

    def _configure_use_sim_time(self, use_sim_time: bool) -> None:
        if self.navigator.has_parameter('use_sim_time'):
            self.navigator.set_parameters([
                Parameter('use_sim_time', Parameter.Type.BOOL, use_sim_time),
            ])
            return

        self.navigator.declare_parameter('use_sim_time', use_sim_time)

    def go_to_waypoint(self, waypoint: WaypointSpec) -> None:
        pose = self.waypoint_to_pose(waypoint)
        self.node.get_logger().info(
            f'[NAV2] Going to {waypoint.name}: '
            f'x={waypoint.x:.2f}, y={waypoint.y:.2f}, yaw={waypoint.yaw:.3f}'
        )
        self.navigator.goToPose(pose)

    def wait_until_done(self) -> bool:
        from nav2_simple_commander.robot_navigator import TaskResult as Nav2TaskResult

        poll_count = 0
        while not self.navigator.isTaskComplete():
            poll_count += 1
            feedback = self.navigator.getFeedback()
            if feedback is not None and poll_count % 10 == 0:
                self.node.get_logger().info('[NAV2] Still navigating...')

        result = self.navigator.getResult()
        if result == Nav2TaskResult.SUCCEEDED:
            self.node.get_logger().info('[NAV2] Navigation succeeded.')
            return True

        self.node.get_logger().error(f'[NAV2] Navigation failed: {result}')
        return False

    def waypoint_to_pose(self, waypoint: WaypointSpec) -> PoseStamped:
        pose = PoseStamped()
        pose.header.frame_id = waypoint.frame_id
        pose.header.stamp = self.navigator.get_clock().now().to_msg()
        pose.pose.position.x = waypoint.x
        pose.pose.position.y = waypoint.y
        pose.pose.position.z = 0.0
        pose.pose.orientation.x = 0.0
        pose.pose.orientation.y = 0.0
        pose.pose.orientation.z = math.sin(waypoint.yaw / 2.0)
        pose.pose.orientation.w = math.cos(waypoint.yaw / 2.0)
        return pose

    def cancel(self) -> None:
        self.navigator.cancelTask()

    def shutdown(self) -> None:
        self.navigator.destroy_node()
