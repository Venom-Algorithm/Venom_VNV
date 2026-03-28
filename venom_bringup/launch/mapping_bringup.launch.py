import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    # Get package directories
    livox_driver_dir = get_package_share_directory('livox_ros_driver2')
    point_lio_dir = get_package_share_directory('point_lio')
    robot_description_dir = get_package_share_directory('venom_robot_description')
    venom_bringup_dir = get_package_share_directory('venom_bringup')

    # Include Livox driver launch
    livox_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(livox_driver_dir, 'launch_ROS2', 'msg_MID360_launch.py')
        )
    )

    # Include Point-LIO headless mapping launch
    point_lio_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(point_lio_dir, 'launch', 'mapping_headless.launch.py')
        )
    )

    # Include robot description (TF tree)
    robot_description_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(robot_description_dir, 'launch', 'scout_mini_description.launch.py')
        )
    )

    # Static TF: map to odom (identity, Point-LIO provides localization)
    map_to_odom_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='map_to_odom_tf',
        arguments=['0', '0', '0', '0', '0', '0', 'map', 'odom']
    )

    # Convert 3D point cloud to 2D laser scan
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
            ('scan', '/scan')
        ]
    )

    # 2D SLAM mapping with slam_toolbox
    slam_toolbox_node = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[{
            'use_sim_time': False,
            'odom_frame': 'odom',
            'map_frame': 'map',
            'base_frame': 'base_link',
            'scan_topic': '/scan',
            'mode': 'mapping',


            'transform_publish_period': 0.0,  # Disable map->odom transform publishing
            'use_scan_matching': False,
            # 地图分辨率
            'resolution': 0.05,

            # 扫描匹配参数
            'minimum_travel_distance': 0.1,

            'map_update_interval': 0.5,
        }]
    )

    # Delay slam_toolbox startup by 10 seconds
    delayed_slam_toolbox = TimerAction(
        period=5.0,
        actions=[slam_toolbox_node]
    )

    # RViz2 for visualization
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', os.path.join(venom_bringup_dir, 'rviz_cfg', 'mapping.rviz')],
        output='screen',
    )

    return LaunchDescription([
        livox_launch,
        point_lio_launch,
        robot_description_launch,
        map_to_odom_tf,
        pointcloud_to_laserscan_node,
        delayed_slam_toolbox,
        rviz_node,
    ])
