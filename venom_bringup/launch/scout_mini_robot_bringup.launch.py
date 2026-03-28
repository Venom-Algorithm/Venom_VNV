"""Scout Mini robot bringup launch file.

Starts the Livox MID360 lidar driver, pointcloud-to-laserscan converter,
Scout Mini base driver, and robot description TF tree. Intended as the
base hardware layer for mapping, relocalization, and navigation tasks.
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    livox_driver_dir = get_package_share_directory('livox_ros_driver2')
    scout_base_dir = get_package_share_directory('scout_base')
    robot_description_dir = get_package_share_directory('venom_robot_description')
    venom_bringup_dir = get_package_share_directory('venom_bringup')

    headless = LaunchConfiguration('headless')

    declare_headless = DeclareLaunchArgument(
        'headless',
        default_value='false',
        description='Do not launch RViz if true'
    )

    livox_config_path = os.path.join(livox_driver_dir, 'config', 'MID360_config.json')

    livox_driver_node = Node(
        package='livox_ros_driver2',
        executable='livox_ros_driver2_node',
        name='livox_lidar_publisher',
        output='screen',
        parameters=[
            {'xfer_format': 0},        # 0-PointCloud2(PointXYZRTL)
            {'multi_topic': 0},
            {'data_src': 0},
            {'publish_freq': 10.0},
            {'output_data_type': 0},
            {'frame_id': 'laser_link'},
            {'lvx_file_path': '/home/livox/livox_test.lvx'},
            {'user_config_path': livox_config_path},
            {'cmdline_input_bd_code': '47MDLAS0020103'},
        ]
    )

    pointcloud_to_laserscan_node = Node(
        package='pointcloud_to_laserscan',
        executable='pointcloud_to_laserscan_node',
        name='pointcloud_to_laserscan',
        parameters=[{
            'target_frame': 'base_link',
            'transform_tolerance': 0.01,
            'min_height': 0.0,
            'max_height': 0.7,
            'angle_min': -3.14159,
            'angle_max': 3.14159,
            'angle_increment': 0.001,
            'scan_time': 0.1,
            'range_min': 0.3,
            'range_max': 50.0,
            'use_inf': True,
        }],
        remappings=[
            ('cloud_in', '/livox/lidar'),
            ('scan', '/scan'),
        ]
    )

    scout_base_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(scout_base_dir, 'launch', 'scout_mini_base.launch.py')
        ),
        launch_arguments={
            'port_name': 'can0',
            'is_scout_mini': 'true',
            'is_omni_wheel': 'false',
        }.items()
    )

    robot_description_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(robot_description_dir, 'launch', 'scout_mini_description.launch.py')
        )
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', os.path.join(venom_bringup_dir, 'rviz_cfg', 'robot.rviz')],
        output='screen',
        condition=UnlessCondition(headless)
    )

    return LaunchDescription([
        declare_headless,
        livox_driver_node,
        pointcloud_to_laserscan_node,
        scout_base_launch,
        robot_description_launch,
        rviz_node,
    ])
