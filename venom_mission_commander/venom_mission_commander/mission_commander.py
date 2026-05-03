import sys
from pathlib import Path

import rclpy
from ament_index_python.packages import PackageNotFoundError, get_package_share_directory
from rcl_interfaces.msg import ParameterDescriptor
from rclpy.node import Node

from venom_mission_commander.mission_loader import MissionLoader
from venom_mission_commander.mission_manager import MissionManager
from venom_mission_commander.models import MissionState, TaskContext, WaypointSpec
from venom_mission_commander.navigator import MockWaypointNavigator, Nav2WaypointNavigator
from venom_mission_commander.task_plugins import TaskPluginRegistry
from venom_mission_commander.task_runner import WaypointTaskRunner


class MissionCommander(Node):
    def __init__(self):
        super().__init__('mission_commander')

        default_config = self._default_config_path()
        self._declare_parameter_if_needed(
            'mission_config',
            default_config,
            ParameterDescriptor(description='Absolute path to mission YAML.'),
        )
        self._declare_parameter_if_needed(
            'use_nav',
            False,
            ParameterDescriptor(description='Use Nav2 instead of mock navigation.'),
        )
        self._declare_parameter_if_needed(
            'mock_nav_delay_sec',
            0.5,
            ParameterDescriptor(description='Mock navigation delay per waypoint.'),
        )
        self._declare_parameter_if_needed(
            'nav2_wait_mode',
            'bt_navigator',
            ParameterDescriptor(description='Nav2 wait mode: bt_navigator or full.'),
        )
        self._declare_parameter_if_needed(
            'use_sim_time',
            False,
            ParameterDescriptor(description='Use Gazebo /clock for simulation runs.'),
        )

        self.loader = MissionLoader()
        self.mission_manager = MissionManager(self.get_logger())
        self.registry = TaskPluginRegistry()
        self.task_runner = WaypointTaskRunner(self.registry, self.mission_manager)
        self.blackboard = {}

        self.mission_config = None
        self.navigator = None

    def configure(self) -> bool:
        config_path = self.get_parameter('mission_config').value
        use_nav = bool(self.get_parameter('use_nav').value)
        mock_nav_delay_sec = float(self.get_parameter('mock_nav_delay_sec').value)
        nav2_wait_mode = str(self.get_parameter('nav2_wait_mode').value)
        use_sim_time = bool(self.get_parameter('use_sim_time').value)

        self.get_logger().info(f'Loading mission config: {config_path}')
        self.mission_config = self.loader.load(config_path)
        self.registry.register_default_plugins(self)
        self.navigator = self._create_navigator(
            use_nav,
            mock_nav_delay_sec,
            nav2_wait_mode,
            use_sim_time,
        )
        self.navigator.wait_until_ready()
        self.mission_manager.create_mission(self.mission_config)

        self.get_logger().info(
            f'Configured mission {self.mission_config.mission_id} with '
            f'{len(self.mission_config.waypoints)} waypoint(s).'
        )
        return True

    def run(self) -> bool:
        if self.mission_config is None or self.navigator is None:
            raise RuntimeError('MissionCommander.configure() must be called before run().')

        loop_count = 0
        self.mission_manager.transition_to(MissionState.RUNNING, 'mission started')

        while rclpy.ok():
            loop_count += 1
            self.mission_manager.save_state(loop_count=loop_count)
            success = self.run_once()

            if not success:
                return False

            if not self.mission_config.loop:
                self.mission_manager.mark_mission_completed()
                return self.mission_manager.state == MissionState.COMPLETED

            self.get_logger().info('Mission loop enabled; restarting route.')

        self.mission_manager.fail('rclpy shutdown requested')
        return False

    def run_once(self) -> bool:
        for waypoint_index, waypoint in enumerate(self.mission_config.waypoints):
            if not self.run_waypoint(waypoint_index, waypoint):
                return False
        return True

    def run_waypoint(self, waypoint_index: int, waypoint: WaypointSpec) -> bool:
        self.get_logger().info(
            f'Waypoint {waypoint_index + 1}/{len(self.mission_config.waypoints)}: '
            f'{waypoint.name}'
        )
        self.mission_manager.mark_waypoint_started(waypoint_index, waypoint.name)

        if waypoint.skip_navigation:
            self.get_logger().info(f'Skipping navigation for waypoint: {waypoint.name}')
            self.mission_manager.save_state(phase='navigation_skipped')
        elif not self.navigate_to_waypoint(waypoint):
            self.handle_navigation_failure(waypoint)
            return False

        context = TaskContext(
            node=self,
            mission_id=self.mission_config.mission_id,
            waypoint=waypoint,
            waypoint_index=waypoint_index,
            task_index=0,
            mission_manager=self.mission_manager,
            blackboard=self.blackboard,
        )
        tasks_ok = self.task_runner.run_tasks(
            context=context,
            tasks=waypoint.tasks,
            stop_on_failure=self.mission_config.stop_on_task_failure,
        )
        if not tasks_ok:
            return False

        self.mission_manager.mark_waypoint_done(waypoint_index, waypoint.name)
        return True

    def navigate_to_waypoint(self, waypoint: WaypointSpec) -> bool:
        self.navigator.go_to_waypoint(waypoint)
        return self.navigator.wait_until_done()

    def handle_navigation_failure(self, waypoint: WaypointSpec) -> None:
        self.navigator.cancel()
        self.mission_manager.fail(f'navigation failed at waypoint: {waypoint.name}')

    def shutdown(self) -> None:
        if self.navigator is not None:
            self.navigator.shutdown()
        self.destroy_node()

    def _declare_parameter_if_needed(
        self,
        name: str,
        value,
        descriptor: ParameterDescriptor,
    ) -> None:
        if self.has_parameter(name):
            return
        self.declare_parameter(name, value, descriptor)

    def _create_navigator(
        self,
        use_nav: bool,
        mock_nav_delay_sec: float,
        nav2_wait_mode: str,
        use_sim_time: bool,
    ):
        if use_nav:
            return Nav2WaypointNavigator(
                self,
                wait_mode=nav2_wait_mode,
                use_sim_time=use_sim_time,
            )
        return MockWaypointNavigator(self, delay_sec=mock_nav_delay_sec)

    def _default_config_path(self) -> str:
        try:
            package_share = Path(get_package_share_directory('venom_mission_commander'))
            return str(package_share / 'config' / 'simple_mission.yaml')
        except PackageNotFoundError:
            package_root = Path(__file__).resolve().parents[1]
            return str(package_root / 'config' / 'simple_mission.yaml')


def main(args=None) -> None:
    rclpy.init(args=args)
    commander = MissionCommander()
    exit_code = 1

    try:
        if commander.configure():
            exit_code = 0 if commander.run() else 1
    except KeyboardInterrupt:
        commander.get_logger().warn('Interrupted by user.')
    except Exception as exc:
        commander.get_logger().error(f'Mission commander failed: {exc}')
    finally:
        commander.get_logger().info(f'Final mission summary: {commander.mission_manager.summarize()}')
        commander.shutdown()
        rclpy.shutdown()

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
