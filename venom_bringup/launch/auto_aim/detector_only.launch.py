import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import TimerAction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    venom_bringup_dir = get_package_share_directory('venom_bringup')
    default_node_params = os.path.join(
        venom_bringup_dir, 'config', 'autoaim', 'node_params.yaml')

    node_params = LaunchConfiguration('node_params')
    debug = LaunchConfiguration('debug')

    declare_args = [
        DeclareLaunchArgument(
            'node_params',
            default_value=default_node_params,
            description='Path to detector/tracker parameter yaml'),
        DeclareLaunchArgument(
            'debug',
            default_value='true',
            description='Enable detector debug outputs'),
    ]

    detector_node = Node(
        package='armor_detector',
        executable='armor_detector_node',
        name='armor_detector',
        emulate_tty=True,
        output='both',
        parameters=[node_params, {'debug': debug}],
    )

    tracker_node = Node(
        package='armor_tracker',
        executable='armor_tracker_node',
        name='armor_tracker',
        emulate_tty=True,
        output='both',
        parameters=[node_params, {'target_frame': 'base_link'}],
    )

    ballistic_solver_node = Node(
        package='auto_aim_solver',
        executable='ballistic_solver',
        name='ballistic_solver',
        output='screen',
        parameters=[
            {
                'map_frame': 'base_link',
                'command_frame': 'base_link',
                'launch_frame': 'barrel_link',
                'camera_frame': 'camera_link',
                'target_topic': '/tracker/target',
                'auto_aim_topic': '/auto_aim',
                'camera_info_topic': '/camera_info',
                'use_live_speed': False,
                'initial_speed': 23.0,
            }
        ],
    )

    return LaunchDescription(
        declare_args + [
            detector_node,
            TimerAction(period=1.5, actions=[tracker_node]),
            TimerAction(period=1.8, actions=[ballistic_solver_node]),
        ]
    )
