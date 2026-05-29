import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder


def generate_launch_description():
    mtc_share = get_package_share_directory("piper_mtc_tasks")
    link_prefix = LaunchConfiguration("link_prefix")
    moveit_config = (
        MoveItConfigsBuilder("piper", package_name="piper_with_gripper_moveit")
        .robot_description(file_path="config/piper.urdf.xacro", mappings={"prefix": link_prefix})
        .robot_description_semantic(file_path="config/piper.srdf", mappings={"prefix": link_prefix})
        .to_moveit_configs()
    )

    default_params = os.path.join(mtc_share, "config", "payload_mount_sweep.yaml")

    return LaunchDescription(
        [
            DeclareLaunchArgument("sweep_params", default_value=default_params),
            DeclareLaunchArgument("link_prefix", default_value="piper_"),
            Node(
                package="piper_mtc_tasks",
                executable="payload_mount_sweep",
                name="payload_mount_sweep",
                output="screen",
                parameters=[
                    LaunchConfiguration("sweep_params"),
                    moveit_config.to_dict(),
                ],
            ),
        ]
    )
