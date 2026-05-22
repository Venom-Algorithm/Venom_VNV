from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
from pathlib import Path


def generate_launch_description():
    config = Path(get_package_share_directory('printed_number_reader')) / 'config' / 'printed_number_reader.yaml'
    return LaunchDescription([
        Node(
            package='printed_number_reader',
            executable='printed_number_reader_node',
            name='printed_number_reader',
            output='screen',
            parameters=[str(config)],
        ),
    ])
