"""Top-level robot bringup entry point.

Selects the appropriate per-robot bringup launch file based on the
'robot_type' argument and delegates to it. This is the canonical launch
file to use when starting up any supported robot platform.

Supported robot types:
  scout_mini  -- AgileX Scout Mini (CAN chassis + rf2o/EKF odometry)
  sentry      -- Sentry platform (no chassis driver, IMU-only EKF)
  hunter_se   -- Hunter SE (TODO: chassis driver not yet integrated)
  infantry    -- Infantry platform (TODO: chassis driver not yet integrated)

Usage:
  ros2 launch venom_bringup robot_bringup.launch.py
  ros2 launch venom_bringup robot_bringup.launch.py robot_type:=sentry
  ros2 launch venom_bringup robot_bringup.launch.py robot_type:=scout_mini headless:=true
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression


def generate_launch_description():
    venom_bringup_dir = get_package_share_directory('venom_bringup')

    robot_type = LaunchConfiguration('robot_type')
    headless = LaunchConfiguration('headless')

    declare_robot_type = DeclareLaunchArgument(
        'robot_type',
        default_value='scout_mini',
        description='Robot platform to bring up: scout_mini | sentry | hunter_se | infantry'
    )
    declare_headless = DeclareLaunchArgument(
        'headless',
        default_value='false',
        description='Do not launch RViz if true'
    )

    scout_mini_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(venom_bringup_dir, 'launch', 'scout_mini', 'robot_bringup.launch.py')
        ),
        launch_arguments={'headless': headless}.items(),
        condition=IfCondition(PythonExpression(["'", robot_type, "' == 'scout_mini'"]))
    )

    sentry_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(venom_bringup_dir, 'launch', 'sentry', 'robot_bringup.launch.py')
        ),
        launch_arguments={'headless': headless}.items(),
        condition=IfCondition(PythonExpression(["'", robot_type, "' == 'sentry'"]))
    )

    hunter_se_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(venom_bringup_dir, 'launch', 'hunter_se', 'robot_bringup.launch.py')
        ),
        launch_arguments={'headless': headless}.items(),
        condition=IfCondition(PythonExpression(["'", robot_type, "' == 'hunter_se'"]))
    )

    infantry_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(venom_bringup_dir, 'launch', 'infantry', 'robot_bringup.launch.py')
        ),
        launch_arguments={'headless': headless}.items(),
        condition=IfCondition(PythonExpression(["'", robot_type, "' == 'infantry'"]))
    )

    return LaunchDescription([
        declare_robot_type,
        declare_headless,
        scout_mini_bringup,
        sentry_bringup,
        hunter_se_bringup,
        infantry_bringup,
    ])
