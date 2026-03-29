"""Scout Mini robot bringup launch file.

Starts the Livox MID360 lidar driver, pointcloud-to-laserscan converter,
Scout Mini base driver, and robot description TF tree. Intended as the
base hardware layer for mapping, relocalization, and navigation tasks.

Odometry source is selectable via the 'odom_source' argument:
  wheel -- Scout Mini wheel encoder odometry (odom -> base_link, ~50 Hz)
  laser -- rf2o laser odometry (odom -> base_link, 10 Hz);
           wheel odometry isolated under scout_odom -> scout_base_link and discarded
  ekf   -- rf2o (10 Hz) fused with Livox IMU (~200 Hz) via EKF (odom -> base_link, 50 Hz);
           wheel odometry isolated under scout_odom -> scout_base_link and discarded
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node


def generate_launch_description():
    livox_driver_dir = get_package_share_directory('livox_ros_driver2')
    scout_base_dir = get_package_share_directory('scout_base')
    robot_description_dir = get_package_share_directory('venom_robot_description')
    venom_bringup_dir = get_package_share_directory('venom_bringup')

    headless = LaunchConfiguration('headless')
    odom_source = LaunchConfiguration('odom_source')

    declare_headless = DeclareLaunchArgument(
        'headless',
        default_value='false',
        description='Do not launch RViz if true'
    )
    declare_odom_source = DeclareLaunchArgument(
        'odom_source',
        default_value='ekf',
        description=(
            "Odometry source: "
            "'wheel' = wheel encoder (odom->base_link, ~50 Hz); "
            "'laser' = rf2o laser odometry (odom->base_link, 10 Hz); "
            "'ekf'   = rf2o + IMU fused by EKF (odom->base_link, 50 Hz)"
        )
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
            'min_height': 0.1,
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

    # In wheel mode:  odom_frame=odom,       odom_topic=odom,       base_frame=base_link
    # In laser/ekf:   odom_frame=scout_odom,  odom_topic=scout_odom, base_frame=scout_base_link
    # Wheel odometry is isolated in laser/ekf modes so it doesn't conflict with the authoritative odom->base_link.
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

    # laser mode: rf2o publishes odom->base_link TF and /odom directly (10 Hz)
    rf2o_laser_node = Node(
        package='rf2o_laser_odometry',
        executable='rf2o_laser_odometry_node',
        name='rf2o_laser_odometry',
        output='screen',
        parameters=[{
            'laser_scan_topic': '/scan',
            'odom_topic': '/odom',
            'publish_tf': True,
            'base_frame_id': 'base_link',
            'odom_frame_id': 'odom',
            'init_pose_from_topic': '',
            'freq': 10.0,
        }],
        condition=IfCondition(PythonExpression(["'", odom_source, "' == 'laser'"]))
    )

    # ekf mode: rf2o publishes raw odometry to /odom_rf2o (no TF) for EKF input
    rf2o_ekf_node = Node(
        package='rf2o_laser_odometry',
        executable='rf2o_laser_odometry_node',
        name='rf2o_laser_odometry',
        output='screen',
        parameters=[{
            'laser_scan_topic': '/scan',
            'odom_topic': '/odom_rf2o',
            'publish_tf': False,
            'base_frame_id': 'base_link',
            'odom_frame_id': 'odom',
            'init_pose_from_topic': '',
            'freq': 10.0,
        }],
        condition=IfCondition(PythonExpression(["'", odom_source, "' == 'ekf'"]))
    )

    # ekf mode: EKF fuses rf2o (10 Hz) + Livox IMU (~200 Hz) -> /odom at 50 Hz
    ekf_scout_config = os.path.join(venom_bringup_dir, 'config', 'ekf_scout.yaml')

    ekf_scout_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        parameters=[ekf_scout_config],
        condition=IfCondition(PythonExpression(["'", odom_source, "' == 'ekf'"]))
    )

    # Delay EKF startup to allow rf2o to stabilize and publish initial /odom_rf2o
    delayed_ekf_scout_node = TimerAction(
        period=2.0,
        actions=[ekf_scout_node]
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
        declare_odom_source,
        livox_driver_node,
        pointcloud_to_laserscan_node,
        scout_base_launch,
        rf2o_laser_node,
        rf2o_ekf_node,
        delayed_ekf_scout_node,
        robot_description_launch,
        rviz_node,
    ])
