import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    """Launch infantry auto-aim stack."""

    pkg_share = get_package_share_directory('venom_bringup')
    description_pkg_share = get_package_share_directory('venom_robot_description')
    default_camera_params = os.path.join(pkg_share, 'config', 'infantry', 'camera_params.yaml')
    default_node_params = os.path.join(pkg_share, 'config', 'infantry', 'node_params.yaml')
    default_serial_params = os.path.join(pkg_share, 'config', 'infantry', 'serial_params.yaml')
    description_launch = os.path.join(
        description_pkg_share, 'launch', 'infantry_description.launch.py'
    )

    camera_params_arg = DeclareLaunchArgument(
        'camera_params',
        default_value=default_camera_params,
        description='Camera parameters file'
    )

    node_params_arg = DeclareLaunchArgument(
        'node_params',
        default_value=default_node_params,
        description='Detector/tracker parameters file'
    )

    serial_params_arg = DeclareLaunchArgument(
        'serial_params',
        default_value=default_serial_params,
        description='Serial driver parameter yaml'
    )

    debug_arg = DeclareLaunchArgument(
        'debug',
        default_value='true',
        description='Enable detector debug outputs'
    )

    robot_description_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(description_launch)
    )

    serial_node = Node(
        package='venom_serial_driver',
        executable='serial_node',
        name='serial_node',
        output='screen',
        parameters=[LaunchConfiguration('serial_params')]
    )

    camera_node = Node(
        package='hik_camera',
        executable='hik_camera_node',
        name='hik_camera',
        output='screen',
        parameters=[LaunchConfiguration('camera_params')]
    )

    detector_node = Node(
        package='armor_detector',
        executable='armor_detector_node',
        name='armor_detector',
        emulate_tty=True,
        output='both',
        parameters=[LaunchConfiguration('node_params'), {'debug': LaunchConfiguration('debug')}]
    )

    tracker_node = Node(
        package='armor_tracker',
        executable='armor_tracker_node',
        name='armor_tracker',
        emulate_tty=True,
        output='both',
        parameters=[LaunchConfiguration('node_params'), {'target_frame': 'base_link'}]
    )

    ballistic_solver_node = Node(
        package='auto_aim_solver',
        executable='ballistic_solver',
        name='ballistic_solver',
        output='screen',
        parameters=[{
            'map_frame': 'base_link',
            'command_frame': 'base_link',
            'launch_frame': 'barrel_link',
            'camera_frame': 'camera_link',
            'target_topic': '/tracker/target',
            'auto_aim_topic': '/auto_aim',
            'camera_info_topic': '/camera_info',
            'use_live_speed': False,
            'initial_speed': 23.0
        }]
    )

    return LaunchDescription([
        camera_params_arg,
        node_params_arg,
        serial_params_arg,
        debug_arg,
        robot_description_launch,
        serial_node,
        camera_node,
        TimerAction(period=1.0, actions=[detector_node]),
        TimerAction(period=1.5, actions=[tracker_node]),
        TimerAction(period=1.8, actions=[ballistic_solver_node])
    ])
