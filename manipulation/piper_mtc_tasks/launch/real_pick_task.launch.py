import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder


def generate_launch_description():
    mtc_share = get_package_share_directory("piper_mtc_tasks")
    piper_moveit_share = get_package_share_directory("piper_with_gripper_moveit")
    piper_share = get_package_share_directory("piper")
    robot_description_share = get_package_share_directory("venom_robot_description")
    link_prefix = LaunchConfiguration("link_prefix")
    moveit_config = (
        MoveItConfigsBuilder("piper", package_name="piper_with_gripper_moveit")
        .robot_description(file_path="config/piper.urdf.xacro", mappings={"prefix": link_prefix})
        .robot_description_semantic(file_path="config/piper.srdf", mappings={"prefix": link_prefix})
        .to_moveit_configs()
    )

    default_params = os.path.join(mtc_share, "config", "real_pick_task.yaml")
    moveit_launch = os.path.join(piper_moveit_share, "launch", "piper_moveit.launch.py")
    rsp_launch = os.path.join(piper_moveit_share, "launch", "rsp.launch.py")
    static_tf_launch = os.path.join(
        piper_moveit_share, "launch", "static_virtual_joint_tfs.launch.py"
    )
    piper_control_launch = os.path.join(
        piper_share, "launch", "start_single_piper.launch.py"
    )
    scoutmini_description_launch = os.path.join(
        robot_description_share, "launch", "scout_mini_description.launch.py"
    )

    declare_params = DeclareLaunchArgument(
        "mtc_params",
        default_value=default_params,
        description="Path to the piper_mtc_tasks parameter file",
    )
    declare_link_prefix = DeclareLaunchArgument("link_prefix", default_value="piper_")
    declare_launch_moveit = DeclareLaunchArgument("launch_moveit", default_value="true")
    declare_launch_rviz = DeclareLaunchArgument("launch_rviz", default_value="false")
    declare_launch_bridge = DeclareLaunchArgument("launch_bridge", default_value="true")
    declare_launch_control = DeclareLaunchArgument(
        "launch_control",
        default_value="false",
        description="Launch the real Piper hardware control node with the correct joint-state remaps.",
    )
    declare_can_port = DeclareLaunchArgument("can_port", default_value="can0")
    declare_auto_enable = DeclareLaunchArgument("auto_enable", default_value="false")
    declare_gripper_exist = DeclareLaunchArgument("gripper_exist", default_value="true")
    declare_gripper_val_mutiple = DeclareLaunchArgument("gripper_val_mutiple", default_value="2")
    declare_invert_gripper_command = DeclareLaunchArgument(
        "invert_gripper_command",
        default_value="false",
        description="Invert hardware gripper width commands when the mounted gripper responds reversed.",
    )
    declare_invert_gripper_feedback = DeclareLaunchArgument(
        "invert_gripper_feedback",
        default_value="false",
        description="Invert hardware gripper feedback decoding when the reported stroke direction is reversed.",
    )
    declare_start_sdk_gripper_limit = DeclareLaunchArgument(
        "start_sdk_gripper_limit",
        default_value="true",
        description="Enable SDK-side gripper software range limiting for the real Piper.",
    )
    declare_sdk_gripper_limit_min_m = DeclareLaunchArgument(
        "sdk_gripper_limit_min_m",
        default_value="0.0",
        description="Minimum total gripper opening width in meters.",
    )
    declare_sdk_gripper_limit_max_m = DeclareLaunchArgument(
        "sdk_gripper_limit_max_m",
        default_value="0.07",
        description="Maximum total gripper opening width in meters.",
    )
    declare_gripper_total_width_limit_m = DeclareLaunchArgument(
        "gripper_total_width_limit_m",
        default_value="0.07",
        description="Local driver clamp for total gripper opening width in meters.",
    )
    declare_send_zero_pose_after_exit_teach = DeclareLaunchArgument(
        "send_zero_pose_after_exit_teach",
        default_value="true",
        description="After exiting teach mode, send one zero pose so the eye-in-hand camera returns to its calibrated view.",
    )
    declare_control_log_level = DeclareLaunchArgument("control_log_level", default_value="info")
    declare_launch_scoutmini_description = DeclareLaunchArgument(
        "launch_scoutmini_description",
        default_value="false",
        description="Launch the ScoutMini chassis static TF description locally.",
    )
    declare_arm_mount_frame = DeclareLaunchArgument(
        "arm_mount_frame",
        default_value="scoutmini_piper_mount_link",
        description="Chassis frame that represents the measured Piper mount location.",
    )
    declare_publish_mount_to_base_tf = DeclareLaunchArgument(
        "publish_mount_to_base_tf",
        default_value="false",
        description=(
            "Publish a static TF from arm_mount_frame to <link_prefix>base_link. "
            "Keep this disabled when the robot description already roots base_link under world."
        ),
    )
    declare_moveit_delay = DeclareLaunchArgument("moveit_delay_sec", default_value="1.0")
    declare_control_delay = DeclareLaunchArgument("control_delay_sec", default_value="0.0")
    declare_bridge_delay = DeclareLaunchArgument("bridge_delay_sec", default_value="0.5")
    declare_server_delay = DeclareLaunchArgument("server_delay_sec", default_value="3.0")

    control_include = TimerAction(
        period=LaunchConfiguration("control_delay_sec"),
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(piper_control_launch),
                launch_arguments={
                    "can_port": LaunchConfiguration("can_port"),
                    "auto_enable": LaunchConfiguration("auto_enable"),
                    "gripper_exist": LaunchConfiguration("gripper_exist"),
                    "gripper_val_mutiple": LaunchConfiguration("gripper_val_mutiple"),
                    "invert_gripper_command": LaunchConfiguration("invert_gripper_command"),
                    "invert_gripper_feedback": LaunchConfiguration("invert_gripper_feedback"),
                    "start_sdk_gripper_limit": LaunchConfiguration("start_sdk_gripper_limit"),
                    "sdk_gripper_limit_min_m": LaunchConfiguration("sdk_gripper_limit_min_m"),
                    "sdk_gripper_limit_max_m": LaunchConfiguration("sdk_gripper_limit_max_m"),
                    "gripper_total_width_limit_m": LaunchConfiguration("gripper_total_width_limit_m"),
                    "send_zero_pose_after_exit_teach": LaunchConfiguration("send_zero_pose_after_exit_teach"),
                    "log_level": LaunchConfiguration("control_log_level"),
                    "command_topic": "/joint_command",
                }.items(),
                condition=IfCondition(LaunchConfiguration("launch_control")),
            )
        ],
    )

    scoutmini_description_include = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(scoutmini_description_launch),
        condition=IfCondition(LaunchConfiguration("launch_scoutmini_description")),
    )

    arm_mount_to_base_tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="scoutmini_piper_mount_to_base_tf",
        arguments=[
            "--x", "0.0",
            "--y", "0.0",
            "--z", "0.0",
            "--roll", "0.0",
            "--pitch", "0.0",
            "--yaw", "0.0",
            "--frame-id", LaunchConfiguration("arm_mount_frame"),
            "--child-frame-id", PythonExpression(["'", LaunchConfiguration("link_prefix"), "base_link'"]),
        ],
        condition=IfCondition(LaunchConfiguration("publish_mount_to_base_tf")),
    )

    bridge_node = TimerAction(
        period=LaunchConfiguration("bridge_delay_sec"),
        actions=[
            Node(
                package="piper",
                executable="joint_trajectory_bridge",
                name="joint_trajectory_bridge",
                output="screen",
                parameters=[
                    {
                        "command_topic": "/joint_command",
                        "state_topic": "/joint_states",
                        "arm_action_name": "/arm_controller/follow_joint_trajectory",
                        "gripper_action_name": "/gripper_controller/follow_joint_trajectory",
                        "position_tolerance": 0.02,
                        "gripper_position_tolerance": 0.005,
                        "goal_time_tolerance_sec": 20.0,
                    }
                ],
                condition=IfCondition(LaunchConfiguration("launch_bridge")),
            )
        ],
    )

    moveit_include = TimerAction(
        period=LaunchConfiguration("moveit_delay_sec"),
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(rsp_launch),
                launch_arguments={
                    "use_sim_time": "false",
                    "link_prefix": LaunchConfiguration("link_prefix"),
                }.items(),
                condition=IfCondition(LaunchConfiguration("launch_moveit")),
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(static_tf_launch),
                launch_arguments={
                    "use_sim_time": "false",
                    "link_prefix": LaunchConfiguration("link_prefix"),
                }.items(),
                condition=IfCondition(LaunchConfiguration("launch_moveit")),
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(moveit_launch),
                launch_arguments={
                    "launch_rviz": LaunchConfiguration("launch_rviz"),
                    "use_sim_time": "false",
                    "capabilities": "move_group/ExecuteTaskSolutionCapability",
                    "link_prefix": LaunchConfiguration("link_prefix"),
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
            declare_link_prefix,
            declare_launch_moveit,
            declare_launch_rviz,
            declare_launch_bridge,
            declare_launch_control,
            declare_can_port,
            declare_auto_enable,
            declare_gripper_exist,
            declare_gripper_val_mutiple,
            declare_invert_gripper_command,
            declare_invert_gripper_feedback,
            declare_start_sdk_gripper_limit,
            declare_sdk_gripper_limit_min_m,
            declare_sdk_gripper_limit_max_m,
            declare_gripper_total_width_limit_m,
            declare_send_zero_pose_after_exit_teach,
            declare_control_log_level,
            declare_launch_scoutmini_description,
            declare_arm_mount_frame,
            declare_publish_mount_to_base_tf,
            declare_moveit_delay,
            declare_control_delay,
            declare_bridge_delay,
            declare_server_delay,
            control_include,
            scoutmini_description_include,
            arm_mount_to_base_tf,
            bridge_node,
            moveit_include,
            server_node,
        ]
    )
