#!/usr/bin/env python3
"""
Health-Aware Multi-Waypoint Navigation Commander

Enhanced version of multi_waypoint_commander with:
- Health monitoring and emergency return
- Mission state persistence and recovery
- Round-trip navigation support
- Generic mission controller framework integration

Usage (after colcon build + source install/setup.bash):
    ros2 run venom_bringup multi_waypoint_commander
    
    # With custom waypoints file:
    ros2 run venom_bringup multi_waypoint_commander \\
        --ros-args -p waypoints_file:=/path/to/waypoints.yaml
    
    # With custom config file:
    ros2 run venom_bringup multi_waypoint_commander \\
        --ros-args -p mission_config_file:=/path/to/mission_config.yaml

Features:
- Automatically returns to base when health < 20%
- Resumes mission when health recovers to 100%
- Saves and restores mission state
- Supports loop navigation (forward and return)
"""

import math
import os
import sys
import time
from typing import Dict, Any, Optional, List, Tuple

import rclpy
import yaml
from ament_index_python.packages import get_package_share_directory
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from rcl_interfaces.msg import ParameterDescriptor
from rclpy.node import Node

# Import mission controller framework
from mission_controller import StateMonitor, MissionManager, MissionState
from plugins import HealthPlugin, NavigationPlugin


class HealthAwareCommander(Node):
    """
    Health-aware waypoint navigation commander.
    
    Integrates health monitoring with navigation to provide:
    - Emergency return when health is low
    - Mission resume when health recovers
    - State persistence across interruptions
    """
    
    def __init__(self):
        super().__init__('health_aware_commander')
        
        # Initialize navigator
        self.navigator = BasicNavigator(node_name='health_aware_navigator')
        
        # Initialize mission controller components
        self.state_monitor = StateMonitor(node_name='state_monitor')
        self.mission_manager = MissionManager(self)
        
        # Initialize plugins
        self.health_plugin: Optional[HealthPlugin] = None
        self.nav_plugin: Optional[NavigationPlugin] = None
        
        # Mission parameters
        self.waypoints_file = ''
        self.config_file = ''
        self.config_data: Dict[str, Any] = {}
        
        # Mission state
        self.mission_active = False
        self.mission_completed = False
        
        # Base position
        self.base_position = PoseStamped()
        self.base_position.header.frame_id = 'map'
        self.base_position.pose.position.x = 0.0
        self.base_position.pose.position.y = 0.0
        self.base_position.pose.position.z = 0.0
        
        self.get_logger().info('HealthAwareCommander initialized')
    
    def configure(self, waypoints_file: str, config_file: str):
        """Configure the commander with files"""
        self.waypoints_file = waypoints_file
        self.config_file = config_file
        
        # Load configuration
        self._load_config()
        
        # Initialize plugins
        self._initialize_plugins()
    
    def _load_config(self):
        """Load mission configuration from YAML file"""
        if not os.path.isfile(self.config_file):
            self.get_logger().warning(f'Config file not found: {self.config_file}')
            self.get_logger().info('Using default configuration')
            return
        
        try:
            with open(self.config_file, 'r') as f:
                self.config_data = yaml.safe_load(f)
            
            self.get_logger().info(f'Loaded configuration from {self.config_file}')
            
            # Extract base position if available
            if 'mission' in self.config_data and 'base_position' in self.config_data['mission']:
                bp = self.config_data['mission']['base_position']
                self.base_position.pose.position.x = bp.get('x', 0.0)
                self.base_position.pose.position.y = bp.get('y', 0.0)
                
        except Exception as e:
            self.get_logger().error(f'Error loading config: {e}')
    
    def _initialize_plugins(self):
        """Initialize all plugins"""
        # Health plugin
        health_config = self.config_data.get('health_plugin', {})
        if health_config.get('enabled', True):
            self.health_plugin = HealthPlugin(
                self.state_monitor,
                self.mission_manager,
                self.navigator
            )
            
            low_threshold = health_config.get('low_threshold', 0.2)
            high_threshold = health_config.get('high_threshold', 1.0)
            
            self.health_plugin.setup(
                low_threshold=low_threshold,
                high_threshold=high_threshold,
                base_position=self.base_position,
                mission_id='navigation'
            )
            
            self.get_logger().info(
                f'Health plugin initialized: low={low_threshold}, high={high_threshold}'
            )
        
        # Navigation plugin
        self.nav_plugin = NavigationPlugin(
            self.navigator,
            self.mission_manager,
            mission_id='navigation'
        )
        
        # Load waypoints
        if self.nav_plugin.load_waypoints_from_file(self.waypoints_file):
            self.get_logger().info(f'Loaded {self.nav_plugin.get_total_waypoints()} waypoints')
        else:
            self.get_logger().fatal('Failed to load waypoints')
            raise RuntimeError('Failed to load waypoints')
        
        # Set mission complete callback
        self.nav_plugin.set_mission_complete_callback(self._on_mission_complete)
    
    def start_mission(self, loop: bool = True):
        """Start the navigation mission"""
        mission_config = self.config_data.get('mission', {})
        loop = mission_config.get('loop', loop)
        
        # Check for saved state
        saved_state = None
        if self.health_plugin:
            saved_state = self.health_plugin.restore_navigation_state()
        
        if saved_state:
            # Restore from saved state
            self.get_logger().info('Restoring mission from saved state')
            current_index = saved_state.get('current_waypoint', 0)
            direction = saved_state.get('direction', 'forward')
            
            # Wait for health to recover before resuming
            self.get_logger().info('Waiting for health recovery before resuming...')
            return False
        
        # Start fresh mission
        self.get_logger().info(f'Starting new mission (loop={loop})')
        self.mission_active = True
        
        return self.nav_plugin.start_mission(loop=loop)
    
    def spin(self):
        """Main spin loop"""
        self.get_logger().info('Starting mission execution...')
        
        # Wait for navigator to be ready
        self.get_logger().info('Waiting for bt_navigator to become active...')
        self.navigator._waitForNodeToActivate('bt_navigator')
        
        # Start mission
        if not self.start_mission():
            self.get_logger().error('Failed to start mission')
            return 1
        
        # Main loop
        rate = self.create_rate(10)  # 10 Hz
        
        while rclpy.ok():
            rclpy.spin_once(self, timeout_sec=0.1)
            
            # Check if task is complete
            if self.navigator.isTaskComplete():
                self._handle_task_complete()
            
            # Check health status and handle return
            if self.health_plugin and self.health_plugin.is_returning():
                self._handle_health_return()
            
            # Check if should resume mission
            if self.health_plugin and self.health_plugin.was_recovered():
                self._handle_mission_resume()
            
            # Check mission status
            if self.mission_completed:
                break
            
            rate.sleep()
        
        # Report result
        return self._report_result()
    
    def _handle_task_complete(self):
        """Handle when navigation task is complete"""
        is_complete, should_continue = self.nav_plugin.update()
        
        if is_complete:
            self.mission_completed = True
        elif should_continue:
            pass  # Continue to next waypoint
        else:
            self.mission_completed = True
    
    def _handle_health_return(self):
        """Handle emergency return due to low health"""
        # Save navigation state
        if self.nav_plugin and self.health_plugin:
            current_index = self.nav_plugin.get_current_waypoint()
            total = self.nav_plugin.get_total_waypoints()
            direction = self.nav_plugin.get_direction()
            waypoint_data = None
            if current_index < len(self.nav_plugin._waypoints):
                waypoint_data = self.nav_plugin._waypoints[current_index]
            
            self.health_plugin.save_navigation_state(
                current_waypoint=current_index,
                total_waypoints=total,
                direction=direction,
                waypoint_data=waypoint_data
            )
    
    def _handle_mission_resume(self):
        """Handle mission resume after health recovery"""
        if not self.health_plugin:
            return
        
        self.get_logger().info('Health recovered, resuming mission...')
        
        # Restore navigation state
        saved_state = self.health_plugin.restore_navigation_state()
        if saved_state:
            current_index = saved_state.get('current_waypoint', 0)
            direction = saved_state.get('direction', 'forward')
            
            self.get_logger().info(
                f'Resuming from waypoint {current_index}, direction={direction}'
            )
            
            # Navigate to the saved waypoint
            if current_index < len(self.nav_plugin._goal_poses):
                goal_pose = [self.nav_plugin._goal_poses[current_index]]
                self.navigator.followWaypoints(goal_pose)
    
    def _on_mission_complete(self):
        """Callback when mission is complete"""
        self.get_logger().info('Mission completed successfully!')
        self.mission_completed = True
    
    def _report_result(self) -> int:
        """Report mission result and return exit code"""
        result = self.navigator.getResult()
        
        if result == TaskResult.SUCCEEDED:
            self.get_logger().info('Mission succeeded!')
            return 0
        elif result == TaskResult.CANCELED:
            self.get_logger().warn('Mission was canceled')
            return 1
        elif result == TaskResult.FAILED:
            self.get_logger().error('Mission failed')
            return 1
        else:
            self.get_logger().error(f'Unknown result: {result}')
            return 1
    
    def cleanup(self):
        """Cleanup resources"""
        if self.state_monitor:
            self.state_monitor.destroy()
        if self.navigator:
            self.navigator.destroy_node()
        self.get_logger().info('Cleanup complete')


def main() -> int:
    """Main entry point"""
    rclpy.init()
    
    try:
        # Create commander
        commander = HealthAwareCommander()
        
        # Resolve file paths
        pkg_share = get_package_share_directory('venom_bringup')
        
        default_waypoints_file = os.path.join(
            pkg_share, 'config', 'scout_mini', 'waypoints.yaml'
        )
        
        default_config_file = os.path.join(
            pkg_share, 'config', 'scout_mini', 'mission_config.yaml'
        )
        
        # Declare parameters
        commander.declare_parameter(
            'waypoints_file',
            default_waypoints_file,
            ParameterDescriptor(description='Path to waypoints YAML file')
        )
        
        commander.declare_parameter(
            'mission_config_file',
            default_config_file,
            ParameterDescriptor(description='Path to mission config YAML file')
        )
        
        # Get parameters
        waypoints_file = commander.get_parameter('waypoints_file').get_parameter_value().string_value
        config_file = commander.get_parameter('mission_config_file').get_parameter_value().string_value
        
        commander.get_logger().info(f'Waypoints file: {waypoints_file}')
        commander.get_logger().info(f'Config file: {config_file}')
        
        # Configure and run
        commander.configure(waypoints_file, config_file)
        
        exit_code = commander.spin()
        
        commander.cleanup()
        
        rclpy.shutdown()
        return exit_code
        
    except Exception as e:
        rclpy.get_logger('health_aware_commander').fatal(f'[ERROR] {e}')
        rclpy.shutdown()
        return 1


if __name__ == '__main__':
    sys.exit(main())
