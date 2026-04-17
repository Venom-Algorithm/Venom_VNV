import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    bridge_launch = os.path.join(
        get_package_share_directory("venom_px4_bridge"),
        "launch",
        "px4_agent_probe.launch.py",
    )

    fmu_prefix = LaunchConfiguration("fmu_prefix")
    bridge_prefix = LaunchConfiguration("bridge_prefix")
    start_agent = LaunchConfiguration("start_agent")
    agent_transport = LaunchConfiguration("agent_transport")
    agent_port = LaunchConfiguration("agent_port")
    agent_device = LaunchConfiguration("agent_device")
    agent_baudrate = LaunchConfiguration("agent_baudrate")

    declare_args = [
        DeclareLaunchArgument(
            "fmu_prefix",
            default_value="/fmu",
            description="PX4 DDS topic namespace prefix.",
        ),
        DeclareLaunchArgument(
            "bridge_prefix",
            default_value="/px4_bridge",
            description="Namespace prefix for bridge outputs.",
        ),
        DeclareLaunchArgument(
            "start_agent",
            default_value="true",
            description="Start MicroXRCEAgent together with the probe stack.",
        ),
        DeclareLaunchArgument(
            "agent_transport",
            default_value="udp4",
            description="Transport argument passed to MicroXRCEAgent.",
        ),
        DeclareLaunchArgument(
            "agent_port",
            default_value="8888",
            description="Port passed to MicroXRCEAgent.",
        ),
        DeclareLaunchArgument(
            "agent_device",
            default_value="/dev/ttyUSB0",
            description="Serial device passed to MicroXRCEAgent when transport=serial.",
        ),
        DeclareLaunchArgument(
            "agent_baudrate",
            default_value="921600",
            description="Serial baudrate passed to MicroXRCEAgent when transport=serial.",
        ),
    ]

    bridge_probe = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(bridge_launch),
        launch_arguments={
            "fmu_prefix": fmu_prefix,
            "bridge_prefix": bridge_prefix,
            "start_agent": start_agent,
            "agent_transport": agent_transport,
            "agent_port": agent_port,
            "agent_device": agent_device,
            "agent_baudrate": agent_baudrate,
        }.items(),
    )

    return LaunchDescription(declare_args + [bridge_probe])
