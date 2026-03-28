"""Mapping bringup with slam_toolbox sync mode.

Runs slam_toolbox in synchronous mapping mode to build and serialize a 2D
occupancy grid. Hardware drivers (Livox, Scout Mini, TF tree, /scan) are
expected to be running via scout_mini_robot_bringup.launch.py beforehand.
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
        executable='sync_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[
            slam_params_file,
            {'use_sim_time': False},
        ]
    )

    delayed_slam_toolbox = TimerAction(
        period=10.0,
        actions=[slam_toolbox_node]
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', os.path.join(venom_bringup_dir, 'rviz_cfg', 'mapping.rviz')],
        output='screen'
    )

    return LaunchDescription([
        declare_slam_params_file,
        delayed_slam_toolbox,
        rviz_node,
    ])
