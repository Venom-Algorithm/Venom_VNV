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
    manipulation_share = get_package_share_directory("venom_manipulation")
    piper_gazebo_share = get_package_share_directory("piper_gazebo")
    piper_moveit_share = get_package_share_directory("piper_with_gripper_moveit")
    moveit_config = MoveItConfigsBuilder(
        "piper", package_name="piper_with_gripper_moveit"
    ).to_moveit_configs()

    default_params = os.path.join(manipulation_share, "config", "sim_pick_place.yaml")
    stand_model = os.path.join(manipulation_share, "models", "pick_place_stand.sdf")
    block_model = os.path.join(manipulation_share, "models", "pick_target_block.sdf")
    gazebo_launch = os.path.join(
        piper_gazebo_share, "launch", "piper_with_gripper", "piper_gazebo.launch.py"
    )
    moveit_launch = os.path.join(piper_moveit_share, "launch", "piper_moveit.launch.py")

    declare_params = DeclareLaunchArgument(
        "manipulation_params",
        default_value=default_params,
        description="Path to the venom_manipulation parameter file",
    )
    declare_launch_gazebo = DeclareLaunchArgument(
        "launch_gazebo",
        default_value="true",
        description="Launch Gazebo simulation",
    )
    declare_launch_moveit = DeclareLaunchArgument(
        "launch_moveit",
        default_value="true",
        description="Launch MoveIt simulation stack",
    )
    declare_use_gazebo_gui = DeclareLaunchArgument(
        "use_gazebo_gui",
        default_value="false",
        description="Launch Gazebo client GUI",
    )
    declare_moveit_delay = DeclareLaunchArgument(
        "moveit_delay_sec",
        default_value="12.0",
        description="Delay before launching MoveIt after Gazebo starts",
    )
    declare_scene_delay = DeclareLaunchArgument(
        "scene_delay_sec",
        default_value="8.0",
        description="Delay before spawning pickup and place scene objects",
    )
    declare_block_delay = DeclareLaunchArgument(
        "block_delay_sec",
        default_value="10.0",
        description="Delay before spawning the pickup block after the table scene is created",
    )
    declare_commander_delay = DeclareLaunchArgument(
        "commander_delay_sec",
        default_value="16.0",
        description="Delay before launching the manipulation commander",
    )
    declare_autostart_task_type = DeclareLaunchArgument(
        "autostart_task_type",
        default_value="0",
        description="Optional task type to execute automatically after commander startup",
    )
    declare_spawn_test_scene = DeclareLaunchArgument(
        "spawn_test_scene",
        default_value="true",
        description="Spawn the pickup block and support stands in Gazebo",
    )
    declare_pickup_stand_x = DeclareLaunchArgument("pickup_stand_x", default_value="0.281")
    declare_pickup_stand_y = DeclareLaunchArgument("pickup_stand_y", default_value="0.0")
    declare_place_stand_x = DeclareLaunchArgument("place_stand_x", default_value="-0.02")
    declare_place_stand_y = DeclareLaunchArgument("place_stand_y", default_value="0.38")
    declare_pick_block_x = DeclareLaunchArgument("pick_block_x", default_value="0.281")
    declare_pick_block_y = DeclareLaunchArgument("pick_block_y", default_value="0.0")
    declare_pick_block_z = DeclareLaunchArgument("pick_block_z", default_value="0.4505")

    gazebo_include = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(gazebo_launch),
        launch_arguments={"use_gui": LaunchConfiguration("use_gazebo_gui")}.items(),
        condition=IfCondition(LaunchConfiguration("launch_gazebo")),
    )

    spawn_tables = TimerAction(
        period=LaunchConfiguration("scene_delay_sec"),
        actions=[
            Node(
                package="gazebo_ros",
                executable="spawn_entity.py",
                name="spawn_pickup_stand",
                output="screen",
                arguments=[
                    "-entity",
                    "pickup_stand",
                    "-file",
                    stand_model,
                    "-timeout",
                    "600.0",
                    "-x",
                    LaunchConfiguration("pickup_stand_x"),
                    "-y",
                    LaunchConfiguration("pickup_stand_y"),
                    "-z",
                    "0.0",
                ],
                condition=IfCondition(LaunchConfiguration("spawn_test_scene")),
            ),
            Node(
                package="gazebo_ros",
                executable="spawn_entity.py",
                name="spawn_place_stand",
                output="screen",
                arguments=[
                    "-entity",
                    "place_stand",
                    "-file",
                    stand_model,
                    "-timeout",
                    "600.0",
                    "-x",
                    LaunchConfiguration("place_stand_x"),
                    "-y",
                    LaunchConfiguration("place_stand_y"),
                    "-z",
                    "0.0",
                ],
                condition=IfCondition(LaunchConfiguration("spawn_test_scene")),
            ),
        ],
    )

    spawn_block = TimerAction(
        period=LaunchConfiguration("block_delay_sec"),
        actions=[
            Node(
                package="gazebo_ros",
                executable="spawn_entity.py",
                name="spawn_pick_target_block",
                output="screen",
                arguments=[
                    "-entity",
                    "pick_target_block",
                    "-file",
                    block_model,
                    "-timeout",
                    "600.0",
                    "-x",
                    LaunchConfiguration("pick_block_x"),
                    "-y",
                    LaunchConfiguration("pick_block_y"),
                    "-z",
                    LaunchConfiguration("pick_block_z"),
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
                launch_arguments={"launch_rviz": "false"}.items(),
                condition=IfCondition(LaunchConfiguration("launch_moveit")),
            )
        ],
    )

    commander_node = TimerAction(
        period=LaunchConfiguration("commander_delay_sec"),
        actions=[
            Node(
                package="venom_manipulation",
                executable="manipulation_commander",
                name="manipulation_commander",
                output="screen",
                parameters=[
                    LaunchConfiguration("manipulation_params"),
                    moveit_config.robot_description,
                    moveit_config.robot_description_semantic,
                    moveit_config.robot_description_kinematics,
                    {
                        "autostart_task_type": LaunchConfiguration("autostart_task_type"),
                        "pickup_stand.x": LaunchConfiguration("pickup_stand_x"),
                        "pickup_stand.y": LaunchConfiguration("pickup_stand_y"),
                        "place_stand.x": LaunchConfiguration("place_stand_x"),
                        "place_stand.y": LaunchConfiguration("place_stand_y"),
                        "pickup_block.x": LaunchConfiguration("pick_block_x"),
                        "pickup_block.y": LaunchConfiguration("pick_block_y"),
                        "pickup_block.z": LaunchConfiguration("pick_block_z"),
                    },
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
            declare_commander_delay,
            declare_autostart_task_type,
            declare_spawn_test_scene,
            declare_pickup_stand_x,
            declare_pickup_stand_y,
            declare_place_stand_x,
            declare_place_stand_y,
            declare_pick_block_x,
            declare_pick_block_y,
            declare_pick_block_z,
            gazebo_include,
            spawn_tables,
            spawn_block,
            moveit_include,
            commander_node,
        ]
    )
