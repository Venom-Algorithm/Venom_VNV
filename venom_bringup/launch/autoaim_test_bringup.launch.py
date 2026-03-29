import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    venom_bringup_dir = get_package_share_directory('venom_bringup')
    launch_sim_dir = get_package_share_directory('launch_sim')
    default_ballistic_config = os.path.join(launch_sim_dir, 'config', 'rm17mm.yaml')

    ballistic_config = LaunchConfiguration('ballistic_config')
    serial_port = LaunchConfiguration('serial_port')
    serial_baud = LaunchConfiguration('serial_baud')
    enable_serial = LaunchConfiguration('enable_serial')

    declare_args = [
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
            description='Whether to start venom_serial_driver during auto-aim tests.'
        ),
    ]

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

    visualizer_node = Node(
        package='launch_sim',
        executable='launch_sim',
        name='launch_sim_node',
        output='screen',
        parameters=[ballistic_config],
    )

    return LaunchDescription(
        declare_args + [
            autoaim_stack,
            TimerAction(period=2.0, actions=[visualizer_node]),
        ]
    )
