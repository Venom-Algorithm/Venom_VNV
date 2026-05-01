import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder


def generate_launch_description():
    mtc_share = get_package_share_directory("piper_mtc_tasks")
    moveit_config = MoveItConfigsBuilder(
        "piper", package_name="piper_with_gripper_moveit"
    ).to_moveit_configs()

    default_params = os.path.join(mtc_share, "config", "ik_frame_sweep.yaml")

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "sweep_params",
                default_value=default_params,
                description="Path to IK frame sweep parameter file",
            ),
            Node(
                package="piper_mtc_tasks",
                executable="ik_frame_sweep",
                name="ik_frame_sweep",
                output="screen",
                parameters=[
                    LaunchConfiguration("sweep_params"),
                    moveit_config.to_dict(),
                ],
            ),
        ]
    )
