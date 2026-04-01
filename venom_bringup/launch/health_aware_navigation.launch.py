"""
Launch file for health-aware waypoint navigation.

This launch file starts the health-aware multi-waypoint commander with:
- Health monitoring and emergency return
- Mission state persistence
- Round-trip navigation

Usage:
    ros2 launch venom_bringup health_aware_navigation.launch.py
    
    # With custom waypoints file:
    ros2 launch venom_bringup health_aware_navigation.launch.py \\
        waypoints_file:=/path/to/waypoints.yaml
    
    # With custom config file:
    ros2 launch venom_bringup health_aware_navigation.launch.py \\
        mission_config_file:=/path/to/mission_config.yaml
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node


def generate_launch_description():
    """Generate launch description for health-aware navigation"""
    
    # Get package share directory
    pkg_share = get_package_share_directory('venom_bringup')
    
    # Default file paths
    default_waypoints_file = os.path.join(
        pkg_share, 'config', 'scout_mini', 'waypoints.yaml'
    )
    
    default_config_file = os.path.join(
        pkg_share, 'config', 'scout_mini', 'mission_config.yaml'
    )
    
    # Declare launch arguments
    waypoints_file_arg = DeclareLaunchArgument(
        'waypoints_file',
        default_value=default_waypoints_file,
        description='Path to waypoints YAML file'
    )
    
    config_file_arg = DeclareLaunchArgument(
        'mission_config_file',
        default_value=default_config_file,
        description='Path to mission configuration YAML file'
    )
    
    # Get launch configurations
    waypoints_file = LaunchConfiguration('waypoints_file')
    config_file = LaunchConfiguration('mission_config_file')
    
    # Create health-aware commander node
    health_aware_commander = Node(
        package='venom_bringup',
        executable='multi_waypoint_commander',
        name='health_aware_commander',
        output='screen',
        parameters=[
            {'waypoints_file': waypoints_file},
            {'mission_config_file': config_file}
        ],
        remappings=[
            ('/game_status', '/game_status'),
            ('/cmd_vel', '/cmd_vel'),
            ('/odom', '/odom')
        ]
    )
    
    # Alternative: Run as a process (uncomment if needed)
    # health_aware_process = ExecuteProcess(
    #     cmd=[
    #         'ros2', 'run', 'venom_bringup', 'multi_waypoint_commander',
    #         '--ros-args',
    #         '-p', ['waypoints_file:=', waypoints_file],
    #         '-p', ['mission_config_file:=', config_file]
    #     ],
    #     output='screen'
    # )
    
    return LaunchDescription([
        waypoints_file_arg,
        config_file_arg,
        health_aware_commander,
        
        # Or use the process version:
        # health_aware_process
    ])
