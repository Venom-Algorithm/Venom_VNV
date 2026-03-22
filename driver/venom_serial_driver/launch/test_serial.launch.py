#!/usr/bin/env python3
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    port_arg = DeclareLaunchArgument(
        'port',
        default_value='/dev/ttyUSB0',
        description='串口设备路径'
    )

    test_process = ExecuteProcess(
        cmd=['python3', 'test/test_serial.py', LaunchConfiguration('port')],
        cwd='/home/venom/venom_ws/src/venom_vnv/driver/venom_serial_driver',
        output='screen'
    )

    return LaunchDescription([
        port_arg,
        test_process
    ])
