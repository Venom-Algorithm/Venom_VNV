import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    default_params = os.path.join(
        get_package_share_directory("flame_arm_tracker"),
        "config",
        "flame_tracking.yaml",
    )
    params_arg = DeclareLaunchArgument(
        "params_file",
        default_value=default_params,
        description="Flame tracking parameter YAML.",
    )
    use_yolo_arg = DeclareLaunchArgument(
        "use_yolo",
        default_value="true",
        description="Use YOLO detector instead of HSV color detector.",
    )

    color_detector_node = Node(
        package="flame_arm_tracker",
        executable="flame_color_detector",
        name="flame_color_detector",
        output="screen",
        parameters=[LaunchConfiguration("params_file")],
        condition=UnlessCondition(LaunchConfiguration("use_yolo")),
    )

    yolo_detector_node = Node(
        package="flame_arm_tracker",
        executable="flame_yolo_detector",
        name="flame_yolo_detector",
        output="screen",
        parameters=[LaunchConfiguration("params_file")],
        condition=IfCondition(LaunchConfiguration("use_yolo")),
    )

    tracker_node = Node(
        package="flame_arm_tracker",
        executable="flame_arm_tracker",
        name="flame_arm_tracker",
        output="screen",
        parameters=[LaunchConfiguration("params_file")],
    )

    return LaunchDescription([
        params_arg,
        use_yolo_arg,
        color_detector_node,
        yolo_detector_node,
        tracker_node,
    ])
