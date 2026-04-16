import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    camera_namespace = LaunchConfiguration("camera_namespace")
    camera_name = LaunchConfiguration("camera_name")
    device_type = LaunchConfiguration("device_type")
    depth_profile = LaunchConfiguration("depth_profile")
    enable_color = LaunchConfiguration("enable_color")
    enable_depth = LaunchConfiguration("enable_depth")
    enable_gyro = LaunchConfiguration("enable_gyro")
    enable_accel = LaunchConfiguration("enable_accel")
    enable_pointcloud = LaunchConfiguration("enable_pointcloud")
    align_depth = LaunchConfiguration("align_depth")
    unite_imu_method = LaunchConfiguration("unite_imu_method")
    use_rviz = LaunchConfiguration("rviz")

    declare_args = [
        DeclareLaunchArgument(
            "camera_namespace",
            default_value="camera",
            description="Namespace for realsense topics.",
        ),
        DeclareLaunchArgument(
            "camera_name",
            default_value="d435i",
            description="Node name for this camera instance.",
        ),
        DeclareLaunchArgument(
            "device_type",
            default_value="d435i",
            description="Attach to devices whose model matches this regex pattern.",
        ),
        DeclareLaunchArgument(
            "depth_profile",
            default_value="640x480x30",
            description="Depth profile in <width>x<height>x<fps> format.",
        ),
        DeclareLaunchArgument(
            "enable_color", default_value="true", description="Enable color stream."
        ),
        DeclareLaunchArgument(
            "enable_depth", default_value="true", description="Enable depth stream."
        ),
        DeclareLaunchArgument(
            "enable_gyro", default_value="true", description="Enable gyro stream."
        ),
        DeclareLaunchArgument(
            "enable_accel", default_value="true", description="Enable accel stream."
        ),
        DeclareLaunchArgument(
            "enable_pointcloud",
            default_value="true",
            description="Enable depth pointcloud output.",
        ),
        DeclareLaunchArgument(
            "align_depth",
            default_value="true",
            description="Align depth image to color image.",
        ),
        DeclareLaunchArgument(
            "unite_imu_method",
            default_value="2",
            description="0:none, 1:copy, 2:linear_interpolation.",
        ),
        DeclareLaunchArgument(
            "rviz", default_value="true", description="Launch RViz2 if true."
        ),
    ]

    rs_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("realsense2_camera"),
                "launch",
                "rs_launch.py",
            )
        ),
        launch_arguments={
            "camera_namespace": camera_namespace,
            "camera_name": camera_name,
            "device_type": device_type,
            "depth_module.depth_profile": depth_profile,
            "enable_color": enable_color,
            "enable_depth": enable_depth,
            "enable_gyro": enable_gyro,
            "enable_accel": enable_accel,
            "pointcloud.enable": enable_pointcloud,
            "align_depth.enable": align_depth,
            "unite_imu_method": unite_imu_method,
        }.items(),
    )

    rviz = Node(
        condition=IfCondition(use_rviz),
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
    )

    return LaunchDescription(
        declare_args
        + [
            rs_launch,
            rviz,
        ]
    )
