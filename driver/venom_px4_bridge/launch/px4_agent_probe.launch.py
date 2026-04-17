import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, OpaqueFunction
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _launch_agent(context):
    transport = LaunchConfiguration("agent_transport").perform(context)
    port = LaunchConfiguration("agent_port").perform(context)
    device = LaunchConfiguration("agent_device").perform(context)
    baudrate = LaunchConfiguration("agent_baudrate").perform(context)

    if transport == "serial":
        cmd = ["MicroXRCEAgent", "serial", "--dev", device, "-b", baudrate]
    else:
        cmd = ["MicroXRCEAgent", transport, "-p", port]

    return [ExecuteProcess(cmd=cmd, output="screen")]


def generate_launch_description():
    bridge_dir = get_package_share_directory("venom_px4_bridge")
    default_config_file = os.path.join(bridge_dir, "config", "px4_bridge.yaml")

    config_file = LaunchConfiguration("config_file")
    fmu_prefix = LaunchConfiguration("fmu_prefix")
    bridge_prefix = LaunchConfiguration("bridge_prefix")
    start_agent = LaunchConfiguration("start_agent")
    agent_transport = LaunchConfiguration("agent_transport")
    agent_port = LaunchConfiguration("agent_port")
    agent_device = LaunchConfiguration("agent_device")
    agent_baudrate = LaunchConfiguration("agent_baudrate")

    declare_args = [
        DeclareLaunchArgument(
            "config_file",
            default_value=default_config_file,
            description="Parameter file for the PX4 bridge nodes.",
        ),
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
            default_value="false",
            description="Start MicroXRCEAgent from this launch file.",
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

    xrce_agent = OpaqueFunction(
        condition=IfCondition(start_agent),
        function=_launch_agent,
    )

    px4_agent_monitor = Node(
        package="venom_px4_bridge",
        executable="px4_agent_monitor",
        name="px4_agent_monitor",
        output="screen",
        parameters=[
            config_file,
            {
                "fmu_prefix": fmu_prefix,
                "bridge_prefix": bridge_prefix,
            },
        ],
    )

    px4_status_adapter = Node(
        package="venom_px4_bridge",
        executable="px4_status_adapter",
        name="px4_status_adapter",
        output="screen",
        parameters=[
            config_file,
            {
                "fmu_prefix": fmu_prefix,
                "bridge_prefix": bridge_prefix,
            },
        ],
    )

    return LaunchDescription(
        declare_args
        + [
            xrce_agent,
            px4_agent_monitor,
            px4_status_adapter,
        ]
    )
