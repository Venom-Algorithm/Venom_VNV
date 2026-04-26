from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    image_topic = LaunchConfiguration("image_topic")
    detections_topic = LaunchConfiguration("detections_topic")
    debug_image_topic = LaunchConfiguration("debug_image_topic")
    publish_debug_image = LaunchConfiguration("publish_debug_image")
    qrcode_only = LaunchConfiguration("qrcode_only")

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "image_topic",
                default_value="/image_raw",
                description="Input image topic consumed by the detector.",
            ),
            DeclareLaunchArgument(
                "detections_topic",
                default_value="/perception/barcodes",
                description="Structured detection output topic.",
            ),
            DeclareLaunchArgument(
                "debug_image_topic",
                default_value="/perception/debug/barcodes",
                description="Annotated debug image topic.",
            ),
            DeclareLaunchArgument(
                "publish_debug_image",
                default_value="true",
                description="Whether to publish annotated debug images.",
            ),
            DeclareLaunchArgument(
                "qrcode_only",
                default_value="true",
                description="Restrict ZBar scanning to QR codes only.",
            ),
            Node(
                package="zbar_ros",
                executable="qr_code_detector",
                name="qr_code_detector",
                output="screen",
                parameters=[
                    {
                        "publish_debug_image": ParameterValue(
                            publish_debug_image, value_type=bool
                        ),
                        "qrcode_only": ParameterValue(qrcode_only, value_type=bool),
                    }
                ],
                remappings=[
                    ("image", image_topic),
                    ("detections", detections_topic),
                    ("debug_image", debug_image_topic),
                ],
            ),
        ]
    )
