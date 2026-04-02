import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    venom_bringup_dir = get_package_share_directory('venom_bringup')
    robot_description_dir = get_package_share_directory('venom_robot_description')

    default_camera_params = os.path.join(
        venom_bringup_dir, 'config', 'infantry', 'camera_params.yaml')
    default_node_params = os.path.join(
        venom_bringup_dir, 'config', 'infantry', 'node_params.yaml')
    default_serial_params = os.path.join(
        venom_bringup_dir, 'config', 'infantry', 'serial_params.yaml')

    camera_params = LaunchConfiguration('camera_params')
    node_params = LaunchConfiguration('node_params')
    serial_params = LaunchConfiguration('serial_params')
    debug = LaunchConfiguration('debug')
    enable_serial = LaunchConfiguration('enable_serial')
    prediction_dt = LaunchConfiguration('prediction_dt')
    initial_speed = LaunchConfiguration('initial_speed')
    use_live_speed = LaunchConfiguration('use_live_speed')
    auto_fire = LaunchConfiguration('auto_fire')

    declare_args = [
        DeclareLaunchArgument(
            'camera_params',
            default_value=default_camera_params,
            description='Path to camera parameter yaml'),
        DeclareLaunchArgument(
            'node_params',
            default_value=default_node_params,
            description='Path to detector/tracker parameter yaml'),
        DeclareLaunchArgument(
            'serial_params',
            default_value=default_serial_params,
            description='Path to serial driver parameter yaml'),
        DeclareLaunchArgument(
            'debug',
            default_value='true',
            description='Enable detector debug outputs'),
        DeclareLaunchArgument(
            'enable_serial',
            default_value='true',
            description='Start venom_serial_driver so the ballistic command reaches the C-board'),
        DeclareLaunchArgument(
            'prediction_dt',
            default_value='0.2',
            description='Prediction horizon in seconds for small-gyro compensation'),
        DeclareLaunchArgument(
            'initial_speed',
            default_value='23.0',
            description='Fallback muzzle speed in m/s when live speed is disabled'),
        DeclareLaunchArgument(
            'use_live_speed',
            default_value='false',
            description='Use /game_status projectile speed feedback when available'),
        DeclareLaunchArgument(
            'auto_fire',
            default_value='false',
            description='Allow solver to set fire=true when tracking is valid'),
    ]

    description_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(robot_description_dir, 'launch', 'infantry_description.launch.py')
        )
    )

    camera_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(venom_bringup_dir, 'launch', 'camera.launch.py')
        ),
        launch_arguments={
            'params_file': camera_params,
        }.items()
    )

    detector_node = Node(
        package='armor_detector',
        executable='armor_detector_node',
        name='armor_detector',
        emulate_tty=True,
        output='both',
        parameters=[node_params, {'debug': debug}],
    )

    tracker_node = Node(
        package='armor_tracker',
        executable='armor_tracker_node',
        name='armor_tracker',
        emulate_tty=True,
        output='both',
        parameters=[node_params, {'target_frame': 'base_link'}],
    )

    ballistic_solver_node = Node(
        package='auto_aim_solver',
        executable='ballistic_solver',
        name='ballistic_solver',
        output='screen',
        parameters=[{
            'aim_mode': 'ballistic',
            'target_source': 'tracker',
            'prediction_dt': prediction_dt,
            'map_frame': 'base_link',
            'command_frame': 'base_link',
            'launch_frame': 'launcher_link',
            'camera_frame': 'camera_link',
            'camera_axes_mode': 'x_down_y_left_z_forward',
            'target_topic': '/tracker/target',
            'auto_aim_topic': '/auto_aim',
            'solution_topic': '/auto_aim/gimbal_cmd',
            'aim_point_topic': '/auto_aim/aim_point',
            'camera_info_topic': '/camera_info',
            'use_live_speed': use_live_speed,
            'initial_speed': initial_speed,
            'auto_fire': auto_fire,
        }],
    )

    serial_node = Node(
        package='venom_serial_driver',
        executable='serial_node',
        name='serial_node',
        output='screen',
        parameters=[serial_params],
        condition=IfCondition(enable_serial)
    )

    return LaunchDescription(
        declare_args + [
            description_launch,
            camera_launch,
            detector_node,
            TimerAction(period=1.2, actions=[serial_node]),
            TimerAction(period=1.5, actions=[tracker_node]),
            TimerAction(period=1.8, actions=[ballistic_solver_node]),
        ]
    )
