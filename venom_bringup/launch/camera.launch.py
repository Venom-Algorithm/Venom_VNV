import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    """Launch Hikrobot camera node."""

    pkg_share = get_package_share_directory('venom_bringup')
    default_params = os.path.join(pkg_share, 'config', 'camera_params.yaml')

    params_arg = DeclareLaunchArgument(
        'params_file',
        default_value=default_params,
        description='Camera parameters file'
    )

    camera_node = Node(
        package='hik_camera',
        executable='hik_camera_node',
        name='hik_camera',
        output='screen',
        parameters=[LaunchConfiguration('params_file')]
    )

    return LaunchDescription([
        params_arg,
        camera_node
    ])
