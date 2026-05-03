"""Launch the USB waypoint simple commander for Scout Mini."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    waypoint_file = LaunchConfiguration('waypoint_file')
    coordinate_mode = LaunchConfiguration('coordinate_mode')
    pose_tracking_topic = LaunchConfiguration('pose_tracking_topic')
    cmd_vel_topic = LaunchConfiguration('cmd_vel_topic')
    map_origin_longitude_deg = LaunchConfiguration('map_origin_longitude_deg')
    map_origin_latitude_deg = LaunchConfiguration('map_origin_latitude_deg')
    map_origin_x_m = LaunchConfiguration('map_origin_x_m')
    map_origin_y_m = LaunchConfiguration('map_origin_y_m')
    map_origin_yaw_rad = LaunchConfiguration('map_origin_yaw_rad')
    final_goal_stop_distance_m = LaunchConfiguration('final_goal_stop_distance_m')
    stuck_timeout_sec = LaunchConfiguration('stuck_timeout_sec')

    return LaunchDescription([
        DeclareLaunchArgument(
            'waypoint_file',
            default_value='',
            description='Absolute path to waypoint.txt. Leave empty to auto-discover from USB.',
        ),
        DeclareLaunchArgument('coordinate_mode', default_value='auto'),
        DeclareLaunchArgument('pose_tracking_topic', default_value='/odometry/global'),
        DeclareLaunchArgument('cmd_vel_topic', default_value='/cmd_vel'),
        DeclareLaunchArgument('map_origin_longitude_deg', default_value='0.0'),
        DeclareLaunchArgument('map_origin_latitude_deg', default_value='0.0'),
        DeclareLaunchArgument('map_origin_x_m', default_value='0.0'),
        DeclareLaunchArgument('map_origin_y_m', default_value='0.0'),
        DeclareLaunchArgument('map_origin_yaw_rad', default_value='0.0'),
        DeclareLaunchArgument('final_goal_stop_distance_m', default_value='10.0'),
        DeclareLaunchArgument('stuck_timeout_sec', default_value='10.0'),
        Node(
            package='venom_bringup',
            executable='simple_commander',
            name='simple_commander',
            output='screen',
            parameters=[
                {'waypoint_file': waypoint_file},
                {'coordinate_mode': coordinate_mode},
                {'pose_tracking_topic': pose_tracking_topic},
                {'cmd_vel_topic': cmd_vel_topic},
                {'map_origin_longitude_deg': map_origin_longitude_deg},
                {'map_origin_latitude_deg': map_origin_latitude_deg},
                {'map_origin_x_m': map_origin_x_m},
                {'map_origin_y_m': map_origin_y_m},
                {'map_origin_yaw_rad': map_origin_yaw_rad},
                {'final_goal_stop_distance_m': final_goal_stop_distance_m},
                {'stuck_timeout_sec': stuck_timeout_sec},
            ],
        ),
    ])
