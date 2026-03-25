import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    nav2_params = os.path.join(
        get_package_share_directory('venom_bringup'),
        'config', 'nav2_params_controller_test.yaml'
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

    planner_server = Node(
        package='nav2_planner',
        executable='planner_server',
        name='planner_server',
        parameters=[nav2_params],
        output='screen'
    )

    controller_server = Node(
        package='nav2_controller',
        executable='controller_server',
        name='controller_server',
        parameters=[nav2_params],
        output='screen'
    )

    lifecycle_manager = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_controller',
        parameters=[{
            'use_sim_time': False,
            'autostart': True,
            'node_names': [
                'local_costmap/local_costmap',
                'global_costmap/global_costmap',
                'planner_server',
                'controller_server'
            ]
        }],
        output='screen'
    )

    return LaunchDescription([
        local_costmap,
        global_costmap,
        planner_server,
        controller_server,
        lifecycle_manager,
    ])
