import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory('venom_robot_description')
    config_file = os.path.join(pkg_share, 'config', 'infantry.yaml')

    return LaunchDescription([
        Node(
            package='venom_robot_description',
            executable='dynamic_tf_publisher',
            name='infantry_description_publisher',
            parameters=[{'config_file': config_file}],
            output='screen',
        )
    ])
