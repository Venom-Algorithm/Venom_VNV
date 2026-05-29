import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder


def generate_launch_description():
    mtc_share = get_package_share_directory("piper_mtc_tasks")
    manipulation_share = get_package_share_directory("venom_manipulation")
    piper_gazebo_share = get_package_share_directory("piper_gazebo")
    piper_moveit_share = get_package_share_directory("piper_with_gripper_moveit")
    moveit_config = MoveItConfigsBuilder(
        "piper", package_name="piper_with_gripper_moveit"
    ).to_moveit_configs()

    default_params = os.path.join(mtc_share, "config", "sim_pick_task.yaml")
    table_model = os.path.join(manipulation_share, "models", "mobile_pick_table.sdf")
    can_model = os.path.join(manipulation_share, "models", "redbull_can.sdf")
    bin_model = os.path.join(manipulation_share, "models", "rear_drop_bin.sdf")
    gazebo_launch = os.path.join(
        piper_gazebo_share, "launch", "piper_with_gripper", "piper_gazebo.launch.py"
    )
    moveit_launch = os.path.join(piper_moveit_share, "launch", "piper_moveit.launch.py")

    declare_params = DeclareLaunchArgument(
        "mtc_params",
        default_value=default_params,
        description="Path to the piper_mtc_tasks parameter file",
    )
    declare_launch_gazebo = DeclareLaunchArgument("launch_gazebo", default_value="true")
    declare_launch_moveit = DeclareLaunchArgument("launch_moveit", default_value="true")
    declare_use_gazebo_gui = DeclareLaunchArgument("use_gazebo_gui", default_value="false")
    declare_moveit_delay = DeclareLaunchArgument("moveit_delay_sec", default_value="12.0")
    declare_scene_delay = DeclareLaunchArgument("scene_delay_sec", default_value="8.0")
    declare_block_delay = DeclareLaunchArgument("block_delay_sec", default_value="10.0")
    declare_server_delay = DeclareLaunchArgument("server_delay_sec", default_value="16.0")
    declare_spawn_test_scene = DeclareLaunchArgument("spawn_test_scene", default_value="true")

    gazebo_include = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(gazebo_launch),
        launch_arguments={"use_gui": LaunchConfiguration("use_gazebo_gui")}.items(),
        condition=IfCondition(LaunchConfiguration("launch_gazebo")),
    )

    spawn_scene = TimerAction(
        period=LaunchConfiguration("scene_delay_sec"),
        actions=[
            Node(
                package="gazebo_ros",
                executable="spawn_entity.py",
                name="spawn_pickup_table",
                output="screen",
                arguments=[
                    "-entity",
                    "pickup_table",
                    "-file",
                    table_model,
                    "-timeout",
                    "600.0",
                    "-x",
                    "0.30",
                    "-y",
                    "-0.14",
                    "-z",
                    "0.0",
                ],
                condition=IfCondition(LaunchConfiguration("spawn_test_scene")),
            ),
            Node(
                package="gazebo_ros",
                executable="spawn_entity.py",
                name="spawn_rear_drop_bin",
                output="screen",
                arguments=[
                    "-entity",
                    "rear_drop_bin",
                    "-file",
                    bin_model,
                    "-timeout",
                    "600.0",
                    "-x",
                    "-0.16",
                    "-y",
                    "-0.12",
                    "-z",
                    "0.0",
                ],
                condition=IfCondition(LaunchConfiguration("spawn_test_scene")),
            ),
        ],
    )

    spawn_can = TimerAction(
        period=LaunchConfiguration("block_delay_sec"),
        actions=[
            Node(
                package="gazebo_ros",
                executable="spawn_entity.py",
                name="spawn_redbull_can",
                output="screen",
                arguments=[
                    "-entity",
                    "redbull_can",
                    "-file",
                    can_model,
                    "-timeout",
                    "600.0",
                    "-x",
                    "0.28",
                    "-y",
                    "-0.07",
                    "-z",
                    "0.12",
                ],
                condition=IfCondition(LaunchConfiguration("spawn_test_scene")),
            ),
        ],
    )

    moveit_include = TimerAction(
        period=LaunchConfiguration("moveit_delay_sec"),
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(moveit_launch),
                launch_arguments={
                    "launch_rviz": "false",
                    "capabilities": "move_group/ExecuteTaskSolutionCapability",
                }.items(),
                condition=IfCondition(LaunchConfiguration("launch_moveit")),
            )
        ],
    )

    server_node = TimerAction(
        period=LaunchConfiguration("server_delay_sec"),
        actions=[
            Node(
                package="piper_mtc_tasks",
                executable="pick_place_server",
                name="pick_place_server",
                output="screen",
                parameters=[
                    LaunchConfiguration("mtc_params"),
                    moveit_config.to_dict(),
                ],
            )
        ],
    )

    return LaunchDescription(
        [
            declare_params,
            declare_launch_gazebo,
            declare_launch_moveit,
            declare_use_gazebo_gui,
            declare_moveit_delay,
            declare_scene_delay,
            declare_block_delay,
            declare_server_delay,
            declare_spawn_test_scene,
            gazebo_include,
            spawn_scene,
            spawn_can,
            moveit_include,
            server_node,
        ]
    )
