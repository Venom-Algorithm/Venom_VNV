"""One-command CRAIC bringup for Scout Mini."""

from __future__ import annotations

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    venom_bringup_dir = get_package_share_directory('venom_bringup')
    robot_description_dir = get_package_share_directory('venom_robot_description')
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')
    scout_base_dir = get_package_share_directory('scout_base')

    use_sim_time = LaunchConfiguration('use_sim_time')
    headless = LaunchConfiguration('headless')
    waypoint_file = LaunchConfiguration('waypoint_file')
    coordinate_mode = LaunchConfiguration('coordinate_mode')
    map_origin_longitude_deg = LaunchConfiguration('map_origin_longitude_deg')
    map_origin_latitude_deg = LaunchConfiguration('map_origin_latitude_deg')
    map_origin_x_m = LaunchConfiguration('map_origin_x_m')
    map_origin_y_m = LaunchConfiguration('map_origin_y_m')
    map_origin_yaw_rad = LaunchConfiguration('map_origin_yaw_rad')
    nav2_params_file = LaunchConfiguration('nav2_params_file')
    ekf_params_file = LaunchConfiguration('ekf_params_file')
    point_lio_params_file = LaunchConfiguration('point_lio_params_file')

    enable_scout_base = LaunchConfiguration('enable_scout_base')
    enable_livox = LaunchConfiguration('enable_livox')
    enable_lio_to_scan = LaunchConfiguration('enable_lio_to_scan')
    enable_rtk = LaunchConfiguration('enable_rtk')
    enable_camera = LaunchConfiguration('enable_camera')
    enable_obstacle_filter = LaunchConfiguration('enable_obstacle_filter')
    enable_yolo = LaunchConfiguration('enable_yolo')
    enable_ipm = LaunchConfiguration('enable_ipm')

    default_waypoint_file = os.path.join(
        venom_bringup_dir, 'config', 'scout_mini', 'waypoint.txt'
    )
    default_nav2_params_file = os.path.join(
        venom_bringup_dir, 'config', 'scout_mini', 'craic_nav2_params.yaml'
    )
    default_ekf_params_file = os.path.join(
        venom_bringup_dir, 'config', 'scout_mini', 'craic_ekf.yaml'
    )
    default_point_lio_params_file = os.path.join(
        venom_bringup_dir, 'config', 'scout_mini', 'point_lio.yaml'
    )
    default_semantic_obstacle_file = os.path.join(
        venom_bringup_dir, 'config', 'scout_mini', 'semantic_obstacle.yaml'
    )
    livox_config_path = os.path.join(
        venom_bringup_dir, 'config', 'scout_mini', 'MID360_config.json'
    )

    arguments = [
        DeclareLaunchArgument('use_sim_time', default_value='false'),
        DeclareLaunchArgument('headless', default_value='false'),
        DeclareLaunchArgument('waypoint_file', default_value=default_waypoint_file),
        DeclareLaunchArgument('coordinate_mode', default_value='geodetic'),
        DeclareLaunchArgument('map_origin_longitude_deg', default_value='0.0'),
        DeclareLaunchArgument('map_origin_latitude_deg', default_value='0.0'),
        DeclareLaunchArgument('map_origin_x_m', default_value='0.0'),
        DeclareLaunchArgument('map_origin_y_m', default_value='0.0'),
        DeclareLaunchArgument('map_origin_yaw_rad', default_value='0.0'),
        DeclareLaunchArgument('nav2_params_file', default_value=default_nav2_params_file),
        DeclareLaunchArgument('ekf_params_file', default_value=default_ekf_params_file),
        DeclareLaunchArgument('point_lio_params_file', default_value=default_point_lio_params_file),
        DeclareLaunchArgument('semantic_obstacle_params_file', default_value=default_semantic_obstacle_file),
        DeclareLaunchArgument('enable_scout_base', default_value='true'),
        DeclareLaunchArgument('enable_livox', default_value='true'),
        DeclareLaunchArgument('enable_lio_to_scan', default_value='true'),
        DeclareLaunchArgument('enable_rtk', default_value='false'),
        DeclareLaunchArgument('enable_camera', default_value='false'),
        DeclareLaunchArgument('enable_obstacle_filter', default_value='false'),
        DeclareLaunchArgument('enable_yolo', default_value='false'),
        DeclareLaunchArgument('enable_ipm', default_value='false'),
        DeclareLaunchArgument('camera_package', default_value='v4l2_camera'),
        DeclareLaunchArgument('camera_executable', default_value='v4l2_camera_node'),
        DeclareLaunchArgument('rtk_package', default_value='nmea_navsat_driver'),
        DeclareLaunchArgument('rtk_executable', default_value='nmea_serial_driver'),
        DeclareLaunchArgument('obstacle_filter_package', default_value='pcl_ros'),
        DeclareLaunchArgument('obstacle_filter_executable', default_value='pointcloud_to_pointcloud'),
        DeclareLaunchArgument('yolo_package', default_value='craic_perception'),
        DeclareLaunchArgument('yolo_executable', default_value='lane_line_detector'),
        DeclareLaunchArgument('ipm_package', default_value='craic_perception'),
        DeclareLaunchArgument('ipm_executable', default_value='ipm_lane_projector'),
    ]

    scout_base_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(scout_base_dir, 'launch', 'scout_mini_base.launch.py')
        ),
        launch_arguments={
            'port_name': 'can0',
            'is_scout_mini': 'true',
            'is_omni_wheel': 'false',
            'odom_frame': 'scout_odom',
            'odom_topic_name': 'scout_odom',
            'base_frame': 'scout_base_link',
        }.items(),
        condition=IfCondition(enable_scout_base),
    )

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
            {'cmdline_input_bd_code': '47MDLAS0020103'},
            {'use_sim_time': use_sim_time},
        ],
        condition=IfCondition(enable_livox),
    )

    point_lio_node = Node(
        package='point_lio',
        executable='pointlio_mapping',
        name='point_lio',
        output='screen',
        parameters=[point_lio_params_file, {'use_sim_time': use_sim_time}],
        remappings=[('/tf', 'tf'), ('/tf_static', 'tf_static')],
    )

    pointcloud_to_laserscan_node = Node(
        package='pointcloud_to_laserscan',
        executable='pointcloud_to_laserscan_node',
        name='pointcloud_to_laserscan',
        parameters=[{
            'use_sim_time': use_sim_time,
            'target_frame': 'base_link',
            'transform_tolerance': 0.2,
            'min_height': 0.05,
            'max_height': 0.8,
            'angle_min': -3.14159,
            'angle_max': 3.14159,
            'angle_increment': 0.001,
            'scan_time': 0.1,
            'range_min': 0.3,
            'range_max': 60.0,
            'use_inf': True,
        }],
        remappings=[
            ('cloud_in', '/cloud_registered'),
            ('scan', '/scan'),
        ],
        condition=IfCondition(enable_lio_to_scan),
    )

    ekf_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        parameters=[ekf_params_file, {'use_sim_time': use_sim_time}],
        remappings=[('odometry/filtered', '/odometry/global')],
    )

    navsat_transform_node = Node(
        package='robot_localization',
        executable='navsat_transform_node',
        name='navsat_transform_node',
        output='screen',
        parameters=[ekf_params_file, {'use_sim_time': use_sim_time}],
        remappings=[
            ('imu/data', '/livox/imu'),
            ('gps/fix', '/fix'),
            ('odometry/filtered', '/odometry/global'),
            ('odometry/gps', '/odometry/gps'),
        ],
    )

    robot_description_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(robot_description_dir, 'launch', 'scout_mini_description.launch.py')
        )
    )

    nav2_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_bringup_dir, 'launch', 'navigation_launch.py')
        ),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'params_file': nav2_params_file,
        }.items(),
    )

    camera_node = Node(
        package=LaunchConfiguration('camera_package'),
        executable=LaunchConfiguration('camera_executable'),
        name='camera_driver',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}],
        condition=IfCondition(enable_camera),
    )

    rtk_node = Node(
        package=LaunchConfiguration('rtk_package'),
        executable=LaunchConfiguration('rtk_executable'),
        name='rtk_driver',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}],
        condition=IfCondition(enable_rtk),
    )

    obstacle_filter_node = Node(
        package=LaunchConfiguration('obstacle_filter_package'),
        executable=LaunchConfiguration('obstacle_filter_executable'),
        name='obstacle_filter',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}],
        remappings=[
            ('input', '/cloud_registered'),
            ('output', '/obstacle_points'),
        ],
        condition=IfCondition(enable_obstacle_filter),
    )

    yolo_lane_node = Node(
        package=LaunchConfiguration('yolo_package'),
        executable=LaunchConfiguration('yolo_executable'),
        name='lane_line_detector',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}],
        remappings=[
            ('image_raw', '/image_raw'),
            ('lane_pixels', '/lane_pixels'),
        ],
        condition=IfCondition(enable_yolo),
    )

    ipm_lane_projector_node = Node(
        package=LaunchConfiguration('ipm_package'),
        executable=LaunchConfiguration('ipm_executable'),
        name='ipm_lane_projector',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}],
        remappings=[
            ('lane_pixels', '/lane_pixels'),
            ('virtual_lane_points', '/virtual_lane_points'),
        ],
        condition=IfCondition(enable_ipm),
    )

    mission_node = Node(
        package='venom_bringup',
        executable='craic_mission_main',
        name='craic_mission_main',
        output='screen',
        parameters=[
            LaunchConfiguration('semantic_obstacle_params_file'),
            {
                'use_sim_time': use_sim_time,
                'waypoint_file': waypoint_file,
                'coordinate_mode': coordinate_mode,
                'map_origin_longitude_deg': map_origin_longitude_deg,
                'map_origin_latitude_deg': map_origin_latitude_deg,
                'map_origin_x_m': map_origin_x_m,
                'map_origin_y_m': map_origin_y_m,
                'map_origin_yaw_rad': map_origin_yaw_rad,
                'pose_tracking_topic': '/odometry/global',
                'cmd_vel_topic': '/cmd_vel',
                'scan_topic': '/scan',
                'waypoint_frame_id': 'map',
                'use_first_waypoint_as_origin': True,
            }
        ],
    )

    delayed_mission_node = TimerAction(period=5.0, actions=[mission_node])

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', os.path.join(venom_bringup_dir, 'rviz_cfg', 'mapping.rviz')],
        output='screen',
        condition=UnlessCondition(headless),
    )

    return LaunchDescription(
        arguments
        + [
            scout_base_launch,
            livox_driver_node,
            camera_node,
            rtk_node,
            robot_description_launch,
            point_lio_node,
            pointcloud_to_laserscan_node,
            obstacle_filter_node,
            yolo_lane_node,
            ipm_lane_projector_node,
            ekf_node,
            navsat_transform_node,
            nav2_launch,
            delayed_mission_node,
            rviz_node,
        ]
    )
