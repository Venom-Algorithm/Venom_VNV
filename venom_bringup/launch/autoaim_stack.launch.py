import os
import yaml

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    venom_bringup_dir = get_package_share_directory('venom_bringup')
    robot_description_dir = get_package_share_directory('venom_robot_description')
    camera_dir = get_package_share_directory('hik_camera')
    serial_dir = get_package_share_directory('venom_serial_driver')
    launch_sim_dir = get_package_share_directory('launch_sim')

    autoaim_config_dir = os.path.join(venom_bringup_dir, 'config', 'autoaim')
    node_params = os.path.join(autoaim_config_dir, 'node_params.yaml')
    launch_params = yaml.safe_load(open(os.path.join(autoaim_config_dir, 'launch_params.yaml')))
    default_ballistic_config = os.path.join(launch_sim_dir, 'config', 'rm42mm.yaml')
    default_camera_params = os.path.join(camera_dir, 'config', 'camera_params.yaml')
    default_camera_info = 'package://venom_bringup/config/autoaim/camera_info.yaml'

    ballistic_config = LaunchConfiguration('ballistic_config')
    serial_port = LaunchConfiguration('serial_port')
    serial_baud = LaunchConfiguration('serial_baud')
    enable_serial = LaunchConfiguration('enable_serial')
    launcher_x = LaunchConfiguration('launcher_x')
    launcher_y = LaunchConfiguration('launcher_y')
    launcher_z = LaunchConfiguration('launcher_z')
    launcher_roll = LaunchConfiguration('launcher_roll')
    launcher_pitch = LaunchConfiguration('launcher_pitch')
    launcher_yaw = LaunchConfiguration('launcher_yaw')
    camera_params_file = LaunchConfiguration('camera_params_file')
    camera_info_url = LaunchConfiguration('camera_info_url')

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
            description='Whether to start venom_serial_driver.'
        ),
        DeclareLaunchArgument(
            'launcher_x',
            default_value='0.15',
            description='Static transform x from gimbal_link to launcher_link.'
        ),
        DeclareLaunchArgument(
            'launcher_y',
            default_value='0.05',
            description='Static transform y from gimbal_link to launcher_link.'
        ),
        DeclareLaunchArgument(
            'launcher_z',
            default_value='0.0',
            description='Static transform z from gimbal_link to launcher_link.'
        ),
        DeclareLaunchArgument(
            'launcher_roll',
            default_value='0.0',
            description='Static transform roll from gimbal_link to launcher_link.'
        ),
        DeclareLaunchArgument(
            'launcher_pitch',
            default_value='0.0',
            description='Static transform pitch from gimbal_link to launcher_link.'
        ),
        DeclareLaunchArgument(
            'launcher_yaw',
            default_value='0.0',
            description='Static transform yaw from gimbal_link to launcher_link.'
        ),
        DeclareLaunchArgument(
            'camera_params_file',
            default_value=default_camera_params,
            description='Path to the Hik camera parameter file.'
        ),
        DeclareLaunchArgument(
            'camera_info_url',
            default_value=default_camera_info,
            description='Camera calibration URL for the Hik camera.'
        ),
    ]

    robot_description = Command([
        'xacro ',
        os.path.join(robot_description_dir, 'urdf', 'rm_gimbal.urdf.xacro'),
        ' xyz:=', launch_params['odom2camera']['xyz'],
        ' rpy:=', launch_params['odom2camera']['rpy'],
    ])

    gimbal_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='gimbal_state_publisher',
        parameters=[{
            'robot_description': robot_description,
            'publish_frequency': 1000.0,
        }],
        output='screen',
    )

    launcher_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='gimbal_to_launcher_tf',
        arguments=[
            '--x', launcher_x,
            '--y', launcher_y,
            '--z', launcher_z,
            '--roll', launcher_roll,
            '--pitch', launcher_pitch,
            '--yaw', launcher_yaw,
            '--frame-id', 'gimbal_link',
            '--child-frame-id', 'launcher_link',
        ],
        output='screen',
    )

    camera_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(camera_dir, 'launch', 'hik_camera.launch.py')
        ),
        launch_arguments={
            'params_file': camera_params_file,
            'camera_info_url': camera_info_url,
        }.items()
    )

    detector_node = Node(
        package='armor_detector',
        executable='armor_detector_node',
        name='armor_detector',
        emulate_tty=True,
        output='both',
        parameters=[node_params],
    )

    tracker_node = Node(
        package='armor_tracker',
        executable='armor_tracker_node',
        name='armor_tracker',
        emulate_tty=True,
        output='both',
        parameters=[node_params],
    )

    ballistic_solver_node = Node(
        package='auto_aim_solver',
        executable='ballistic_solver',
        name='ballistic_solver',
        output='screen',
        parameters=[ballistic_config],
    )

    serial_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(serial_dir, 'launch', 'serial_driver.launch.py')
        ),
        launch_arguments={
            'port_name': serial_port,
            'baud_rate': serial_baud,
        }.items(),
        condition=IfCondition(enable_serial)
    )

    return LaunchDescription(
        declare_args + [
            gimbal_state_publisher,
            launcher_tf,
            camera_launch,
            detector_node,
            TimerAction(period=1.5, actions=[tracker_node]),
            TimerAction(period=1.8, actions=[ballistic_solver_node]),
            TimerAction(period=1.2, actions=[serial_launch]),
        ]
    )
