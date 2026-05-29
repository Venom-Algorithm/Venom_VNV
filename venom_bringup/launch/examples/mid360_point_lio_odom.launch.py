import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    venom_bringup_dir = get_package_share_directory("venom_bringup")

    point_lio_cfg = LaunchConfiguration("point_lio_cfg")

    livox_user_config = os.path.join(
        venom_bringup_dir, "config", "examples", "MID360_config.json"
    )
    default_point_lio_cfg = os.path.join(
        venom_bringup_dir, "config", "examples", "point_lio_online_odom.yaml"
    )

    declare_point_lio_cfg = DeclareLaunchArgument(
        "point_lio_cfg",
        default_value=default_point_lio_cfg,
        description="Path to Point-LIO online odometry config yaml.",
    )

    livox_driver = Node(
        package="livox_ros_driver2",
        executable="livox_ros_driver2_node",
        name="livox_lidar_publisher",
        output="screen",
        parameters=[
            {"xfer_format": 1},
            {"multi_topic": 0},
            {"data_src": 0},
            {"publish_freq": 10.0},
            {"output_data_type": 0},
            {"frame_id": "base_link"},
            {"lvx_file_path": "/home/livox/livox_test.lvx"},
            {"user_config_path": livox_user_config},
            {"cmdline_input_bd_code": "livox0000000001"},
        ],
    )

    point_lio = Node(
        package="point_lio",
        executable="pointlio_mapping",
        name="point_lio",
        output="screen",
        parameters=[point_lio_cfg],
        remappings=[("/tf", "tf"), ("/tf_static", "tf_static")],
    )

    return LaunchDescription(
        [
            declare_point_lio_cfg,
            livox_driver,
            point_lio,
        ]
    )
