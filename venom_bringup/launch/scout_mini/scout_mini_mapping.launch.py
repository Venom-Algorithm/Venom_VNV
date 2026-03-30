"""Scout Mini mapping bringup launch file.

Full mapping stack for the Scout Mini platform:
  1. Livox MID360 driver  -- publishes /livox/lidar and /livox/imu
  2. Point-LIO            -- 3D LiDAR-inertial odometry; publishes /cloud_registered
                             and odom->base_link TF; saves PCD to ~/Point-LIO/PCD/
  3. pointcloud_to_laserscan -- converts /cloud_registered to /scan (2D)
  4. slam_toolbox (async) -- builds a 2D occupancy map from /scan
  5. nav2_bringup         -- navigation stack

Run this file to build a map from scratch. When done, save the slam_toolbox
map via: ros2 service call /slam_toolbox/save_map slam_toolbox/srv/SaveMap
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.conditions import UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node


def generate_launch_description():
    scout_base_dir = get_package_share_directory('scout_base')
    venom_bringup_dir = get_package_share_directory('venom_bringup')
    robot_description_dir = get_package_share_directory('venom_robot_description')
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')

    headless = LaunchConfiguration('headless')
    odom_source = LaunchConfiguration('odom_source')
    nav2_params_file = LaunchConfiguration('nav2_params_file')

    declare_headless = DeclareLaunchArgument(
        'headless',
        default_value='false',
        description='Do not launch RViz if true'
    )
    declare_odom_source = DeclareLaunchArgument(
        'odom_source',
        default_value='ekf',
        description=(
            "Odometry source for scout_base only: "
            "'wheel' = wheel encoder (odom->base_link); "
            "'laser/ekf' = isolate wheel odom under scout_odom->scout_base_link "
            "to avoid conflict with Point-LIO odom->base_link"
        )
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
            {'xfer_format': 1},
            {'multi_topic': 0},
            {'data_src': 0},
            {'publish_freq': 10.0},
            {'output_data_type': 0},
            {'frame_id': 'base_link'},
            {'lvx_file_path': '/home/livox/livox_test.lvx'},
            {'user_config_path': livox_config_path},
            {'cmdline_input_bd_code': '47MDLAS0020103'},
        ]
    )

    # In wheel mode:  odom_frame=odom,       odom_topic=odom,       base_frame=base_link
    # In laser/ekf:   odom_frame=scout_odom, odom_topic=scout_odom, base_frame=scout_base_link
    # Wheel odometry is isolated in laser/ekf modes so it doesn't conflict with
    # the authoritative odom->base_link from Point-LIO.
    scout_base_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(scout_base_dir, 'launch', 'scout_mini_base.launch.py')
        ),
        launch_arguments={
            'port_name': 'can0',
            'is_scout_mini': 'true',
            'is_omni_wheel': 'false',
            'odom_frame': PythonExpression(
                ["'odom' if '", odom_source, "' == 'wheel' else 'scout_odom'"]
            ),
            'odom_topic_name': PythonExpression(
                ["'odom' if '", odom_source, "' == 'wheel' else 'scout_odom'"]
            ),
            'base_frame': PythonExpression(
                ["'base_link' if '", odom_source, "' == 'wheel' else 'scout_base_link'"]
            ),
        }.items()
    )

    # ---------------------------------------------------------------------------
    # 2. Point-LIO (3D LiDAR-inertial odometry + PCD save)
    # ---------------------------------------------------------------------------
    point_lio_config = os.path.join(venom_bringup_dir, 'config', 'scout_mini', 'point_lio_mapping.yaml')

    point_lio_node = Node(
        package='point_lio',
        executable='pointlio_mapping',
        name='point_lio',
        output='screen',
        parameters=[point_lio_config],
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
    # 4. slam_toolbox (async mapping, map->odom TF disabled -- Point-LIO owns it)
    # ---------------------------------------------------------------------------
    slam_toolbox_config = os.path.join(venom_bringup_dir, 'config', 'scout_mini', 'slam_toolbox_mapping.yaml')

    slam_toolbox_node = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[
            slam_toolbox_config,
            {'use_sim_time': False},
        ]
    )

    # Delay slam_toolbox until Point-LIO has published the first odom->base_link TF.
    delayed_slam_toolbox = TimerAction(
        period=10.0,
        actions=[slam_toolbox_node]
    )

    # ---------------------------------------------------------------------------
    # 5. Robot description TF tree
    # ---------------------------------------------------------------------------
    robot_description_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(robot_description_dir, 'launch', 'scout_mini_description.launch.py')
        )
    )

    # ---------------------------------------------------------------------------
    # 6. Navigation stack
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
        declare_odom_source,
        declare_nav2_params,
        livox_driver_node,
        scout_base_launch,
        point_lio_node,
        pointcloud_to_laserscan_node,
        delayed_slam_toolbox,
        robot_description_launch,
        nav2_launch,
        rviz_node,
    ])
