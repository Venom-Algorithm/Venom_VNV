import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
import yaml


def create_handeye_tf_node(context):
    handeye_file = LaunchConfiguration("handeye_file").perform(context)
    with open(handeye_file, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)

    params = data["handeye"]["ros__parameters"]
    translation = [str(value) for value in params["translation_xyz"]]
    rotation = [str(value) for value in params["rotation_xyzw"]]
    parent_frame = params["parent_frame"]
    child_frame = params["child_frame"]

    return [
        Node(
            package="tf2_ros",
            executable="static_transform_publisher",
            name="hand_to_camera_static_tf",
            arguments=[
                *translation,
                *rotation,
                parent_frame,
                child_frame,
            ],
        )
    ]


def generate_launch_description():
    fusion_share = get_package_share_directory("grasp_target_fusion")
    flame_share = get_package_share_directory("flame_arm_tracker")
    bringup_share = get_package_share_directory("venom_bringup")
    mtc_share = get_package_share_directory("piper_mtc_tasks")
    piper_share = get_package_share_directory("piper")

    d435i_launch = os.path.join(bringup_share, "launch", "examples", "d435i_test.launch.py")
    piper_control_launch = os.path.join(piper_share, "launch", "start_single_piper.launch.py")
    real_pick_task_launch = os.path.join(mtc_share, "launch", "real_pick_task.launch.py")
    fusion_config = os.path.join(fusion_share, "config", "grasp_target_fusion.yaml")
    color_box_config = os.path.join(flame_share, "config", "color_box_detection.yaml")
    workspace_handeye_file = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "handeye",
            "hand_to_camera_optical_frame_2026-05-23.yaml",
        )
    )
    handeye_file = (
        workspace_handeye_file
        if os.path.exists(workspace_handeye_file)
        else os.path.join(
            fusion_share, "handeye", "hand_to_camera_optical_frame_2026-05-23.yaml"
        )
    )
    mtc_params = os.path.join(mtc_share, "config", "real_pick_task_vision_test.yaml")

    return LaunchDescription([
        DeclareLaunchArgument("camera_namespace", default_value="camera"),
        DeclareLaunchArgument("camera_name", default_value="d435i"),
        DeclareLaunchArgument("depth_profile", default_value="640x480x30"),
        DeclareLaunchArgument("enable_color", default_value="true"),
        DeclareLaunchArgument("enable_depth", default_value="true"),
        DeclareLaunchArgument("enable_gyro", default_value="false"),
        DeclareLaunchArgument("enable_accel", default_value="false"),
        DeclareLaunchArgument("can_port", default_value="can0"),
        DeclareLaunchArgument("auto_enable", default_value="true"),
        DeclareLaunchArgument("gripper_exist", default_value="true"),
        DeclareLaunchArgument("gripper_val_mutiple", default_value="2"),
        DeclareLaunchArgument("invert_gripper_command", default_value="true"),
        DeclareLaunchArgument("invert_gripper_feedback", default_value="false"),
        DeclareLaunchArgument("send_zero_pose_after_exit_teach", default_value="true"),
        DeclareLaunchArgument("launch_piper_control", default_value="true"),
        DeclareLaunchArgument("launch_moveit_stack", default_value="true"),
        DeclareLaunchArgument("launch_scoutmini_description", default_value="false"),
        DeclareLaunchArgument("arm_mount_frame", default_value="scoutmini_piper_mount_link"),
        DeclareLaunchArgument("publish_mount_to_base_tf", default_value="false"),
        DeclareLaunchArgument("link_prefix", default_value="piper_"),
        DeclareLaunchArgument("handeye_file", default_value=handeye_file),
        DeclareLaunchArgument("mtc_params", default_value=mtc_params),
        DeclareLaunchArgument("launch_yolo_detector", default_value="false"),
        DeclareLaunchArgument("launch_yolo_bridge", default_value="false"),
        DeclareLaunchArgument("launch_color_box_detector", default_value="false"),
        DeclareLaunchArgument(
            "yolo_model_path",
            default_value="yolov8n.pt",
        ),
        DeclareLaunchArgument("yolo_image_topic", default_value="/camera/d435i/color/image_raw"),
        DeclareLaunchArgument("yolo_output_topic", default_value="/perception/detections"),
        DeclareLaunchArgument("yolo_allowed_classes", default_value="black_block,white_block,black,white"),
        DeclareLaunchArgument("yolo_min_confidence", default_value="0.7"),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(d435i_launch),
            launch_arguments={
                "camera_namespace": LaunchConfiguration("camera_namespace"),
                "camera_name": LaunchConfiguration("camera_name"),
                "depth_profile": LaunchConfiguration("depth_profile"),
                "enable_color": LaunchConfiguration("enable_color"),
                "enable_depth": LaunchConfiguration("enable_depth"),
                "enable_gyro": LaunchConfiguration("enable_gyro"),
                "enable_accel": LaunchConfiguration("enable_accel"),
                "enable_pointcloud": "false",
                "rviz": "false",
                "align_depth": "true",
            }.items(),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(piper_control_launch),
            launch_arguments={
                "can_port": LaunchConfiguration("can_port"),
                "auto_enable": LaunchConfiguration("auto_enable"),
                "gripper_exist": LaunchConfiguration("gripper_exist"),
                "gripper_val_mutiple": LaunchConfiguration("gripper_val_mutiple"),
                "invert_gripper_command": LaunchConfiguration("invert_gripper_command"),
                "invert_gripper_feedback": LaunchConfiguration("invert_gripper_feedback"),
                "send_zero_pose_after_exit_teach": LaunchConfiguration("send_zero_pose_after_exit_teach"),
            }.items(),
            condition=IfCondition(LaunchConfiguration("launch_piper_control")),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(real_pick_task_launch),
            launch_arguments={
                "mtc_params": LaunchConfiguration("mtc_params"),
                "launch_moveit": LaunchConfiguration("launch_moveit_stack"),
                "launch_rviz": "false",
                "launch_bridge": "true",
                "launch_scoutmini_description": LaunchConfiguration("launch_scoutmini_description"),
                "arm_mount_frame": LaunchConfiguration("arm_mount_frame"),
                "publish_mount_to_base_tf": LaunchConfiguration("publish_mount_to_base_tf"),
                "link_prefix": LaunchConfiguration("link_prefix"),
                "invert_gripper_feedback": LaunchConfiguration("invert_gripper_feedback"),
                "send_zero_pose_after_exit_teach": LaunchConfiguration("send_zero_pose_after_exit_teach"),
            }.items(),
            condition=IfCondition(LaunchConfiguration("launch_moveit_stack")),
        ),
        OpaqueFunction(function=create_handeye_tf_node),
        Node(
            package="grasp_target_fusion",
            executable="grasp_target_fusion",
            name="grasp_target_fusion",
            output="screen",
            parameters=[fusion_config],
        ),
        Node(
            package="flame_arm_tracker",
            executable="color_box_detector",
            name="color_box_detector",
            output="screen",
            parameters=[color_box_config],
            condition=IfCondition(LaunchConfiguration("launch_color_box_detector")),
        ),
        Node(
            package="yolo_detector",
            executable="yolo_node",
            name="yolo_detector",
            output="screen",
            parameters=[
                {
                    "model_path": LaunchConfiguration("yolo_model_path"),
                    "image_topic": LaunchConfiguration("yolo_image_topic"),
                    "output_topic": LaunchConfiguration("yolo_output_topic"),
                }
            ],
            condition=IfCondition(LaunchConfiguration("launch_yolo_detector")),
        ),
        Node(
            package="grasp_target_fusion",
            executable="yolo_detection_bridge",
            name="yolo_detection_bridge",
            output="screen",
            parameters=[
                {
                    "input_topic": LaunchConfiguration("yolo_output_topic"),
                    "output_topic": "/perception/detections_2d",
                    "output_array_topic": "/perception/detections_2d_array",
                    "default_frame_id": "d435i_color_optical_frame",
                    "allowed_classes": LaunchConfiguration("yolo_allowed_classes"),
                    "min_confidence": LaunchConfiguration("yolo_min_confidence"),
                }
            ],
            condition=IfCondition(LaunchConfiguration("launch_yolo_bridge")),
        ),
    ])
