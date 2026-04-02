"""Sentry navigation bringup launch file.

Navigation stack for the Sentry platform:
  1. Livox MID360 driver  -- publishes /livox/lidar and /livox/imu
  2. venom_serial_driver  -- Sentry chassis driver
  3. Point-LIO            -- 3D LiDAR-inertial odometry; publishes /cloud_registered
                             and odom->base_link TF
  4. pointcloud_to_laserscan -- converts /cloud_registered to /scan (2D)
  5. nav2_bringup         -- navigation stack with map_server (static map)
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
    venom_bringup_dir = get_package_share_directory('venom_bringup')
    robot_description_dir = get_package_share_directory('venom_robot_description')
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')

    headless = LaunchConfiguration('headless')
    nav2_params_file = LaunchConfiguration('nav2_params_file')
    map_yaml_file = LaunchConfiguration('map_yaml_file')

    declare_headless = DeclareLaunchArgument(
        'headless',
        default_value='false',
        description='Do not launch RViz if true'
    )
    declare_nav2_params = DeclareLaunchArgument(
        'nav2_params_file',
        default_value=os.path.join(venom_bringup_dir, 'config', 'sentry', 'nav2_params.yaml'),
        description='Path to nav2 parameters file'
    )
    declare_map_yaml = DeclareLaunchArgument(
        'map_yaml_file',
        default_value=os.path.join(venom_bringup_dir, 'map', 'rmul2026_map.yaml'),
        description='Path to static map yaml for map_server'
    )

    # ---------------------------------------------------------------------------
    # 1. venom_serial_driver (Sentry chassis driver)
    # ---------------------------------------------------------------------------
    serial_config = os.path.join(venom_bringup_dir, 'config', 'sentry', 'serial_params.yaml')

    serial_driver_node = Node(
        package='venom_serial_driver',
        executable='serial_node',
        name='serial_node',
        output='screen',
        parameters=[serial_config]
    )

    # ---------------------------------------------------------------------------
    # 2. Livox MID360 driver
    # ---------------------------------------------------------------------------
    livox_config_path = os.path.join(venom_bringup_dir, 'config', 'sentry', 'MID360_config.json')

    livox_driver_node = Node(
        package='livox_ros_driver2',
        executable='livox_ros_driver2_node',
        name='livox_lidar_publisher',
        output='screen',
        parameters=[
            {'xfer_format': 1},
            {'multi_topic': 0},
            {'data_src': 0},
            {'publish_freq': 10.0},
            {'output_data_type': 0},
            {'frame_id': 'base_link'},
            {'lvx_file_path': '/home/livox/livox_test.lvx'},
            {'user_config_path': livox_config_path},
            {'cmdline_input_bd_code': '47MDN6D0030233'},
        ]
    )

    # ---------------------------------------------------------------------------
    # 3. Point-LIO (3D LiDAR-inertial odometry)
    # ---------------------------------------------------------------------------
    point_lio_config = os.path.join(venom_bringup_dir, 'config', 'sentry', 'point_lio_mapping.yaml')

    point_lio_node = Node(
        package='point_lio',
        executable='pointlio_mapping',
        name='point_lio',
        output='screen',
        parameters=[point_lio_config],
        remappings=[('/tf', 'tf'), ('/tf_static', 'tf_static')],
    )

    # ---------------------------------------------------------------------------
    # 4. pointcloud_to_laserscan -- /cloud_registered -> /scan
    # ---------------------------------------------------------------------------
    pointcloud_to_laserscan_node = Node(
        package='pointcloud_to_laserscan',
        executable='pointcloud_to_laserscan_node',
        name='pointcloud_to_laserscan',
        parameters=[{
            'target_frame': 'base_link',
            'transform_tolerance': 0.2,
            'min_height': 0.05,
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
            ('cloud_in', '/cloud_registered'),
            ('scan', '/scan'),
        ]
    )

    # ---------------------------------------------------------------------------
    # 5. Robot description TF tree
    # ---------------------------------------------------------------------------
    robot_description_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(robot_description_dir, 'launch', 'sentry_description.launch.py')
        )
    )

    # ---------------------------------------------------------------------------
    # 6. Navigation stack (map_server via static map yaml)
    # ---------------------------------------------------------------------------
    nav2_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_bringup_dir, 'launch', 'navigation_launch.py')
        ),
        launch_arguments={
            'use_sim_time': 'false',
            'params_file': nav2_params_file,
            'map': map_yaml_file,
        }.items()
    )

    # ---------------------------------------------------------------------------
    # 7. RViz
    # ---------------------------------------------------------------------------
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', os.path.join(venom_bringup_dir, 'rviz_cfg', 'mapping.rviz')],
        output='screen',
        condition=UnlessCondition(headless)
    )

    return LaunchDescription([
        declare_headless,
        declare_nav2_params,
        declare_map_yaml,
        serial_driver_node,
        livox_driver_node,
        point_lio_node,
        pointcloud_to_laserscan_node,
        robot_description_launch,
        nav2_launch,
        rviz_node,
    ])
