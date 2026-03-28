import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import EnvironmentVariable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node


def generate_launch_description():
    livox_driver_dir = get_package_share_directory('livox_ros_driver2')
    point_lio_dir = get_package_share_directory('point_lio')
    small_gicp_dir = get_package_share_directory('small_gicp_relocalization')
    robot_description_dir = get_package_share_directory('venom_robot_description')

    pcd_file = LaunchConfiguration('pcd_file')
    rviz_config = LaunchConfiguration('rviz_config')
    map_2d_file = LaunchConfiguration('map_2d_file')

    declare_pcd_file = DeclareLaunchArgument(
        'pcd_file',
        default_value=PathJoinSubstitution([
            EnvironmentVariable("HOME"),
            "venom_ws/src/venom_vnv/lio/Point-LIO/PCD/scans.pcd"
        ]),
        description='Path to prior map PCD file'
    )
    declare_rviz_config = DeclareLaunchArgument(
        'rviz_config',
        default_value=PathJoinSubstitution([
            EnvironmentVariable("HOME"),
            "venom_ws/src/venom_vnv/venom_bringup/rviz_cfg/relocalization.rviz"
        ]),
        description='Path to RViz config file'
    )
    declare_map_2d_file = DeclareLaunchArgument(
        'map_2d_file',
        default_value=PathJoinSubstitution([
            EnvironmentVariable("HOME"),
            "venom_ws/src/venom_vnv/lio/Point-LIO/PCD/map_2d"
        ]),
        description='Path to 2D slam_toolbox serialized map (without extension)'
    )

    robot_description_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(robot_description_dir, 'launch', 'scout_mini_description.launch.py')
        )
    )

    livox_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(livox_driver_dir, 'launch_ROS2', 'msg_MID360_launch.py')
        )
    )

    point_lio_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(point_lio_dir, 'launch', 'point_lio.launch.py')
        ),
        launch_arguments={'rviz': 'False'}.items()
    )

    prior_map_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(small_gicp_dir, 'launch', 'prior_map_publisher.launch.py')
        ),
        launch_arguments={'pcd_file': pcd_file}.items()
    )

    relocalization_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(small_gicp_dir, 'launch', 'relocalization.launch.py')
        ),
        launch_arguments={'prior_pcd_file': pcd_file}.items()
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
            ('cloud_in', '/cloud_registered'),
            ('scan', '/scan')
        ]
    )

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
            'transform_publish_period': 0.0,
        }]
    )

    delayed_slam_toolbox = TimerAction(
        period=15.0,
        actions=[slam_toolbox_localization_node]
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz',
        arguments=['-d', rviz_config],
        output='screen'
    )

    return LaunchDescription([
        declare_pcd_file,
        declare_rviz_config,
        declare_map_2d_file,
        livox_launch,
        point_lio_launch,
        robot_description_launch,
        prior_map_launch,
        relocalization_launch,
        pointcloud_to_laserscan_node,
        delayed_slam_toolbox,
        rviz_node,
    ])
