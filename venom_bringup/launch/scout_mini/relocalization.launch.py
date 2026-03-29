"""Scout Mini relocalization bringup launch file.

Full relocalization + navigation stack for the Scout Mini platform:
  1. Livox MID360 driver          -- publishes /livox/lidar and /livox/imu
  2. Point-LIO                    -- 3D LiDAR-inertial odometry; publishes /cloud_registered
                                     and odom->base_link TF
  3. pointcloud_to_laserscan      -- converts /cloud_registered to /scan (2D)
  4. small_gicp prior map publisher -- publishes the saved PCD as /prior_map
  5. small_gicp relocalization    -- estimates map->odom transform from prior PCD
  6. slam_toolbox (localization)  -- loads a serialized 2D map for costmap use
  7. nav2_bringup                 -- navigation stack
  8. Robot description TF tree

Required args:
  pcd_file    -- path to the 3D prior map PCD (from Point-LIO PCD save)
  map_2d_file -- path to the slam_toolbox serialized map (without extension)
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.conditions import UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import EnvironmentVariable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node


def generate_launch_description():
    venom_bringup_dir = get_package_share_directory('venom_bringup')
    robot_description_dir = get_package_share_directory('venom_robot_description')
    small_gicp_dir = get_package_share_directory('small_gicp_relocalization')
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')

    headless = LaunchConfiguration('headless')
    pcd_file = LaunchConfiguration('pcd_file')
    map_2d_file = LaunchConfiguration('map_2d_file')
    nav2_params_file = LaunchConfiguration('nav2_params_file')

    declare_headless = DeclareLaunchArgument(
        'headless',
        default_value='false',
        description='Do not launch RViz if true'
    )
    declare_pcd_file = DeclareLaunchArgument(
        'pcd_file',
        default_value=PathJoinSubstitution([
            EnvironmentVariable('HOME'),
            'venom_ws/src/venom_vnv/lio/Point-LIO/PCD/scans.pcd'
        ]),
        description='Path to prior 3D map PCD file (produced by Point-LIO during mapping)'
    )
    declare_map_2d_file = DeclareLaunchArgument(
        'map_2d_file',
        default_value=PathJoinSubstitution([
            EnvironmentVariable('HOME'),
            'venom_ws/src/venom_vnv/lio/Point-LIO/PCD/map_2d'
        ]),
        description='Path to slam_toolbox serialized map (without file extension)'
    )
    declare_nav2_params = DeclareLaunchArgument(
        'nav2_params_file',
        default_value=os.path.join(venom_bringup_dir, 'config', 'scout_mini', 'nav2_params.yaml'),
        description='Path to nav2 parameters file'
    )

    # ---------------------------------------------------------------------------
    # 1. Livox MID360 driver
    # ---------------------------------------------------------------------------
    livox_config_path = os.path.join(venom_bringup_dir, 'config', 'scout_mini', 'MID360_config.json')

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
            {'frame_id': 'laser_link'},
            {'lvx_file_path': '/home/livox/livox_test.lvx'},
            {'user_config_path': livox_config_path},
            {'cmdline_input_bd_code': '47MDLAS0020103'},
        ]
    )

    # ---------------------------------------------------------------------------
    # 2. Point-LIO (3D LiDAR-inertial odometry, PCD save disabled in localization)
    # ---------------------------------------------------------------------------
    point_lio_config = os.path.join(venom_bringup_dir, 'config', 'scout_mini', 'point_lio.yaml')

    point_lio_node = Node(
        package='point_lio',
        executable='pointlio_mapping',
        name='point_lio',
        output='screen',
        parameters=[
            point_lio_config,
            {'pcd_save.pcd_save_en': False},  # Do not overwrite the prior map
        ],
        remappings=[('/tf', 'tf'), ('/tf_static', 'tf_static')],
    )

    # ---------------------------------------------------------------------------
    # 3. pointcloud_to_laserscan -- /cloud_registered -> /scan
    # ---------------------------------------------------------------------------
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
            ('cloud_in', '/cloud_registered'),
            ('scan', '/scan'),
        ]
    )

    # ---------------------------------------------------------------------------
    # 4. Prior map publisher (PCD -> /prior_map topic)
    # ---------------------------------------------------------------------------
    prior_map_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(small_gicp_dir, 'launch', 'prior_map_publisher.launch.py')
        ),
        launch_arguments={'pcd_file': pcd_file}.items()
    )

    # ---------------------------------------------------------------------------
    # 5. small_gicp relocalization (map->odom TF)
    # ---------------------------------------------------------------------------
    relocalization_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(small_gicp_dir, 'launch', 'relocalization.launch.py')
        ),
        launch_arguments={'prior_pcd_file': pcd_file}.items()
    )

    # ---------------------------------------------------------------------------
    # 6. slam_toolbox (localization mode -- loads serialized 2D map)
    # ---------------------------------------------------------------------------
    slam_toolbox_localization_node = Node(
        package='slam_toolbox',
        executable='localization_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[{
            'use_sim_time': False,
            'odom_frame': 'odom',
            'map_frame': 'map',
            'base_frame': 'base_link',
            'scan_topic': '/scan',
            'mode': 'localization',
            'map_file_name': map_2d_file,
            'transform_publish_period': 0.0,  # small_gicp owns map->odom
        }]
    )

    # Delay until small_gicp has established the map->odom transform.
    delayed_slam_toolbox = TimerAction(
        period=15.0,
        actions=[slam_toolbox_localization_node]
    )

    # ---------------------------------------------------------------------------
    # 7. Robot description TF tree
    # ---------------------------------------------------------------------------
    robot_description_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(robot_description_dir, 'launch', 'scout_mini_description.launch.py')
        )
    )

    # ---------------------------------------------------------------------------
    # 8. Navigation stack
    # ---------------------------------------------------------------------------
    nav2_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_bringup_dir, 'launch', 'navigation_launch.py')
        ),
        launch_arguments={
            'use_sim_time': 'false',
            'params_file': nav2_params_file,
        }.items()
    )

    # ---------------------------------------------------------------------------
    # 9. RViz
    # ---------------------------------------------------------------------------
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', os.path.join(venom_bringup_dir, 'rviz_cfg', 'relocalization.rviz')],
        output='screen',
        condition=UnlessCondition(headless)
    )

    return LaunchDescription([
        declare_headless,
        declare_pcd_file,
        declare_map_2d_file,
        declare_nav2_params,
        livox_driver_node,
        point_lio_node,
        pointcloud_to_laserscan_node,
        prior_map_launch,
        relocalization_launch,
        robot_description_launch,
        nav2_launch,
        delayed_slam_toolbox,
        rviz_node,
    ])
