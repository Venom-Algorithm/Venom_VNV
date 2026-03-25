import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    nav2_params = os.path.join(
        get_package_share_directory('venom_bringup'),
        'config', 'nav2_params_costmap_test.yaml'
    )

    local_costmap = Node(
        package='nav2_costmap_2d',
        executable='nav2_costmap_2d',
        name='local_costmap',
        namespace='local_costmap',
        parameters=[nav2_params],
        output='screen'
    )

    global_costmap = Node(
        package='nav2_costmap_2d',
        executable='nav2_costmap_2d',
        name='global_costmap',
        namespace='global_costmap',
        parameters=[nav2_params],
        output='screen'
    )

    lifecycle_manager = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_costmap',
        parameters=[{
            'use_sim_time': False,
            'autostart': True,
            'node_names': ['local_costmap/local_costmap', 'global_costmap/global_costmap']
        }],
        output='screen'
    )

    return LaunchDescription([
        local_costmap,
        global_costmap,
        lifecycle_manager,
    ])
