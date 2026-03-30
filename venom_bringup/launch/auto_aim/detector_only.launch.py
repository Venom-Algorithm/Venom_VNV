import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
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

    return LaunchDescription(declare_args + [detector_node])
