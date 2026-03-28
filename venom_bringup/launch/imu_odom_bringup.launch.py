"""IMU odometry bringup launch file.

Starts the Livox MID360 lidar driver (which also publishes /livox/imu),
the imu_odom_publisher node that integrates IMU data into odom->base_link TF
and /odom topic, and a static transform from livox_frame to base_link.
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    livox_driver_dir = get_package_share_directory('livox_ros_driver2')
    livox_config_path = os.path.join(livox_driver_dir, 'config', 'MID360_config.json')

    # Livox MID360 driver — publishes /livox/lidar and /livox/imu
    livox_driver_node = Node(
        package='livox_ros_driver2',
        executable='livox_ros_driver2_node',
        name='livox_lidar_publisher',
        output='screen',
        parameters=[
            {'xfer_format': 0},
            {'multi_topic': 0},
            {'data_src': 0},
            {'publish_freq': 10.0},
            {'output_data_type': 0},
            {'frame_id': 'livox_frame'},
            {'lvx_file_path': '/home/livox/livox_test.lvx'},
            {'user_config_path': livox_config_path},
            {'cmdline_input_bd_code': '47MDLAS0020103'},
        ]
    )

    # IMU dead-reckoning node — publishes /odom and odom->base_link TF
    imu_odom_node = Node(
        package='venom_bringup',
        executable='imu_odom_publisher',
        name='imu_odom_publisher',
        output='screen',
    )

    # Static TF: livox_frame -> base_link
    # Adjust translation/rotation to match actual sensor mounting position.
    livox_to_base_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='livox_to_base_link_tf',
        # args: x y z yaw pitch roll parent child
        arguments=['0', '0', '0', '0', '0', '0', 'base_link', 'livox_frame'],
    )

    return LaunchDescription([
        livox_driver_node,
        imu_odom_node,
        livox_to_base_tf,
    ])
