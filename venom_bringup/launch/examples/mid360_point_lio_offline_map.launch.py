import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    venom_bringup_dir = get_package_share_directory("venom_bringup")

    point_lio_cfg = LaunchConfiguration("point_lio_cfg")
    bag_path = LaunchConfiguration("bag_path")
    output_pcd_path = LaunchConfiguration("output_pcd_path")

    default_point_lio_cfg = os.path.join(
        venom_bringup_dir, "config", "examples", "point_lio_offline_map.yaml"
    )
    default_output_pcd_path = os.path.join(
        os.path.expanduser("~"), "venom_bags", "point_lio_maps", "offline_map.pcd"
    )

    declare_point_lio_cfg = DeclareLaunchArgument(
        "point_lio_cfg",
        default_value=default_point_lio_cfg,
        description="Path to Point-LIO offline map config yaml.",
    )
    declare_bag_path = DeclareLaunchArgument(
        "bag_path",
        default_value="",
        description="Input rosbag2 directory for offline Point-LIO mapping.",
    )
    declare_output_pcd_path = DeclareLaunchArgument(
        "output_pcd_path",
        default_value=default_output_pcd_path,
        description="Output PCD path for offline Point-LIO mapping.",
    )

    point_lio = Node(
        package="point_lio",
        executable="pointlio_mapping",
        name="point_lio_offline_map",
        output="screen",
        parameters=[
            point_lio_cfg,
            {
                "lio.offline.bag_path": bag_path,
                "lio.offline.output_pcd_path": output_pcd_path,
            },
        ],
        remappings=[("/tf", "tf"), ("/tf_static", "tf_static")],
    )

    return LaunchDescription(
        [
            declare_point_lio_cfg,
            declare_bag_path,
            declare_output_pcd_path,
            point_lio,
        ]
    )
