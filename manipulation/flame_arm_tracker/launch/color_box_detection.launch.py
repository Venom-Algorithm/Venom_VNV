import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    default_params = os.path.join(
        get_package_share_directory("flame_arm_tracker"),
        "config",
        "color_box_detection.yaml",
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "params_file",
                default_value=default_params,
                description="Color box detection parameter YAML.",
            ),
            Node(
                package="flame_arm_tracker",
                executable="color_box_detector",
                name="color_box_detector",
                output="screen",
                parameters=[LaunchConfiguration("params_file")],
            ),
        ]
    )
