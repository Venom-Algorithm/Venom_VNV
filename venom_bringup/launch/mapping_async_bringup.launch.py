"""Mapping bringup with slam_toolbox async mode.

Runs slam_toolbox in asynchronous mapping mode to build and serialize a 2D
occupancy grid. Hardware drivers (Livox, Scout Mini, TF tree, /scan) are
expected to be running via scout_mini_robot_bringup.launch.py beforehand.

Async mode drops scans when the solver is busy, which is more suitable for
real-time operation on hardware with limited CPU resources.
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, TimerAction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    venom_bringup_dir = get_package_share_directory('venom_bringup')

    slam_params_file = LaunchConfiguration('slam_params_file')

    declare_slam_params_file = DeclareLaunchArgument(
        'slam_params_file',
        default_value=os.path.join(venom_bringup_dir, 'config', 'mapper_params_sync.yaml'),
        description='Full path to slam_toolbox parameters file'
    )

    slam_toolbox_node = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[
            slam_params_file,
            {'use_sim_time': False},
        ]
    )

    # Delay startup to allow odom -> base_link TF (from rf2o or wheel odometry)
    # to become available before slam_toolbox begins processing scans.
    delayed_slam_toolbox = TimerAction(
        period=5.0,
        actions=[slam_toolbox_node]
    )

    return LaunchDescription([
        declare_slam_params_file,
        delayed_slam_toolbox,
    ])
