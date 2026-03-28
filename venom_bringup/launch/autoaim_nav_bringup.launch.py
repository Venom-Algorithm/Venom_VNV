import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import EnvironmentVariable, LaunchConfiguration, PathJoinSubstitution


def generate_launch_description():
    venom_bringup_dir = get_package_share_directory('venom_bringup')
    scout_base_dir = get_package_share_directory('scout_base')
    launch_sim_dir = get_package_share_directory('launch_sim')

    default_ballistic_config = os.path.join(launch_sim_dir, 'config', 'rm42mm.yaml')

    pcd_file = LaunchConfiguration('pcd_file')
    map_2d_file = LaunchConfiguration('map_2d_file')
    rviz_config = LaunchConfiguration('rviz_config')
    ballistic_config = LaunchConfiguration('ballistic_config')
    serial_port = LaunchConfiguration('serial_port')
    serial_baud = LaunchConfiguration('serial_baud')
    enable_serial = LaunchConfiguration('enable_serial')

    declare_args = [
        DeclareLaunchArgument(
            'pcd_file',
            default_value=PathJoinSubstitution([
                EnvironmentVariable('HOME'),
                'venom_ws/src/venom_vnv/lio/Point-LIO/PCD/scans.pcd'
            ]),
            description='Path to prior map PCD file.'
        ),
        DeclareLaunchArgument(
            'map_2d_file',
            default_value=PathJoinSubstitution([
                EnvironmentVariable('HOME'),
                'venom_ws/src/venom_vnv/lio/Point-LIO/PCD/map_2d'
            ]),
            description='Path to 2D slam_toolbox serialized map without extension.'
        ),
        DeclareLaunchArgument(
            'rviz_config',
            default_value=PathJoinSubstitution([
                EnvironmentVariable('HOME'),
                'venom_ws/src/venom_vnv/venom_bringup/rviz_cfg/relocalization.rviz'
            ]),
            description='Path to RViz config file.'
        ),
        DeclareLaunchArgument(
            'ballistic_config',
            default_value=default_ballistic_config,
            description='Path to the ballistic solver YAML config.'
        ),
        DeclareLaunchArgument(
            'serial_port',
            default_value='/dev/ttyUSB0',
            description='Serial port used by venom_serial_driver.'
        ),
        DeclareLaunchArgument(
            'serial_baud',
            default_value='921600',
            description='Serial baud rate used by venom_serial_driver.'
        ),
        DeclareLaunchArgument(
            'enable_serial',
            default_value='true',
            description='Whether to start venom_serial_driver.'
        ),
    ]

    scout_base_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(scout_base_dir, 'launch', 'scout_mini_base.launch.py')
        ),
        launch_arguments={
            'port_name': 'can0',
            'is_scout_mini': 'true',
            'is_omni_wheel': 'false',
            'odom_frame': 'odom',
            'odom_topic_name': 'odom',
            'base_frame': 'base_link',
        }.items()
    )

    relocalization_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(venom_bringup_dir, 'launch', 'relocalization_bringup.launch.py')
        ),
        launch_arguments={
            'pcd_file': pcd_file,
            'map_2d_file': map_2d_file,
            'rviz_config': rviz_config,
        }.items()
    )

    nav_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(venom_bringup_dir, 'launch', 'nav_test.launch.py')
        )
    )

    autoaim_stack = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(venom_bringup_dir, 'launch', 'autoaim_stack.launch.py')
        ),
        launch_arguments={
            'ballistic_config': ballistic_config,
            'serial_port': serial_port,
            'serial_baud': serial_baud,
            'enable_serial': enable_serial,
        }.items()
    )

    return LaunchDescription(
        declare_args + [
            scout_base_launch,
            relocalization_launch,
            nav_launch,
            autoaim_stack,
        ]
    )
