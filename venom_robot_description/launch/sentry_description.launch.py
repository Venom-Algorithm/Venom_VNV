import os
import yaml

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory('venom_robot_description')
    config_file = os.path.join(pkg_share, 'config', 'sentry.yaml')

    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)

    nodes = []
    for tf in config.get('transforms', []):
        parent = tf['parent_frame']
        child = tf['child_frame']
        tx, ty, tz = tf['translation']
        roll, pitch, yaw = tf['rotation']

        nodes.append(
            Node(
                package='tf2_ros',
                executable='static_transform_publisher',
                name=f'static_tf_{parent}_to_{child}'.replace('/', '_'),
                arguments=[
                    '--x', str(tx),
                    '--y', str(ty),
                    '--z', str(tz),
                    '--roll', str(roll),
                    '--pitch', str(pitch),
                    '--yaw', str(yaw),
                    '--frame-id', parent,
                    '--child-frame-id', child,
                ],
                output='screen',
            )
        )

    return LaunchDescription(nodes)
