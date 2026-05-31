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
    moveit_config = MoveItConfigsBuilder(
        "piper", package_name="piper_with_gripper_moveit"
    ).robot_description(
        file_path="config/piper.urdf.xacro",
        mappings={"prefix": link_prefix},
    ).robot_description_semantic(
        file_path="config/piper.srdf",
        mappings={"prefix": link_prefix},
    ).to_moveit_configs()
    moveit_params = moveit_config.to_dict()
    kinematics = dict(moveit_params.get("robot_description_kinematics", {}))
    kinematics["arm"] = {
        "kinematics_solver": "kdl_kinematics_plugin/KDLKinematicsPlugin",
        "kinematics_solver_search_resolution": 0.005,
        "kinematics_solver_timeout": 0.08,
    }
    moveit_params["robot_description_kinematics"] = kinematics

    default_params = os.path.join(
        mtc_share, "config", "task_pose_reachability_probe.yaml"
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "probe_params",
                default_value=default_params,
                description="Path to task pose reachability probe parameter file",
            ),
            DeclareLaunchArgument("link_prefix", default_value="piper_"),
            Node(
                package="piper_mtc_tasks",
                executable="task_pose_reachability_probe",
                name="task_pose_reachability_probe",
                output="screen",
                parameters=[
                    LaunchConfiguration("probe_params"),
                    moveit_params,
                ],
            ),
        ]
    )
