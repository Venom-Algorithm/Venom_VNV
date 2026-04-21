<div align="center">

# Venom VNV

A general-purpose ROS 2 Humble platform that brings navigation, manipulation, auto-aim, localization, simulation, and multi-vehicle integration into one workspace.

<p>
  <a href="./README.md">
    <img src="https://img.shields.io/badge/README-%E4%B8%AD%E6%96%87-111111?style=for-the-badge" alt="README Chinese">
  </a>
  <a href="./README_EN.md">
    <img src="https://img.shields.io/badge/README-English-2563eb?style=for-the-badge" alt="README English">
  </a>
</p>

<p>
  <a href="https://venom-algorithm.github.io/Venom_VNV/">
    <img src="https://img.shields.io/badge/Docs-%E4%B8%AD%E6%96%87-c2410c?style=flat-square" alt="Docs Chinese">
  </a>
  <a href="https://venom-algorithm.github.io/Venom_VNV/en/">
    <img src="https://img.shields.io/badge/Docs-English-1d4ed8?style=flat-square" alt="Docs English">
  </a>
  <img src="https://img.shields.io/badge/Ubuntu-22.04-E95420?style=flat-square&logo=ubuntu&logoColor=white" alt="Ubuntu 22.04">
  <img src="https://img.shields.io/badge/ROS%202-Humble-22314E?style=flat-square&logo=ros&logoColor=white" alt="ROS 2 Humble">
</p>

</div>

## Overview

Venom VNV is not a single-task competition repository. It is intended to be a reusable robotics base for multiple robot forms and task types, including:

- UGVs
- UAVs
- USVs
- general mobile robots

The goal is to standardize the engineering pieces that keep repeating across projects:

- hardware and sensor integration
- detection, tracking, auto-aim, and task perception
- LIO, odometry, and relocalization
- path planners, controllers, and manipulation motion planning
- waypoint, behavior-tree, monitor, and mission-management logic
- system bringup and interface conventions
- simulation and regression workflows

## Quick Links

- Documentation: [venom-algorithm.github.io/Venom_VNV](https://venom-algorithm.github.io/Venom_VNV/)
- Quick Start: [Quick Start](https://venom-algorithm.github.io/Venom_VNV/en/quick_start)
- Modules & Interfaces: [Modules & Interfaces](https://venom-algorithm.github.io/Venom_VNV/en/interface_reference)
- Development Notes: [Development Notes](https://venom-algorithm.github.io/Venom_VNV/en/development)
- Chinese docs: [中文文档](https://venom-algorithm.github.io/Venom_VNV/)

## Seven-Layer Architecture

| Layer | Main directories | Purpose |
| --- | --- | --- |
| Driver | `driver/` | Livox, Hikrobot camera, chassis, arm, serial, and PX4 bridge integrations |
| Perception | `perception/` | auto-aim detection, tracking, and solving pipelines |
| Localization | `localization/` | Point-LIO, Fast-LIO, rf2o, and small_gicp relocalization |
| Planning | `planning/` | navigation planners, controllers, and MoveIt-side motion planning |
| Mission | `mission/` | `venom_waypoint`, BT, monitor, and mission-management packages |
| System | `venom_bringup`, `venom_robot_description` | bringup, mode composition, TF description, and robot assembly |
| Simulation | `simulation/venom_nav_simulation` | standalone simulation workspace for navigation and localization |

## Core Components

| Category | Representative packages | Purpose |
| --- | --- | --- |
| Sensors and drivers | `livox_ros_driver2`, `ros2_hik_camera`, `venom_serial_driver` | LiDAR, industrial camera, and serial communication |
| Vehicle and arm drivers | `scout_ros2`, `hunter_ros2`, `ugv_sdk`, `piper_ros` | chassis, low-level SDK, and arm-side integration |
| Flight bridge | `driver/venom_px4_bridge` | PX4, DDS Agent, and ROS 2 bridge path |
| Perception | `perception/rm_auto_aim` | detection, tracking, solving, and interface definitions |
| Localization | `Point-LIO`, `Fast-LIO`, `rf2o_laser_odometry` | unified 3D / 2D odometry outputs |
| Relocalization | `small_gicp_relocalization` | recover `map -> odom` from point-cloud registration |
| Planning | `planning/` | entry point for `venom_eagle_planner`, `venom_teb_controller`, and `venom_moveit_grasp`-style packages |
| Mission | `mission/` | entry point for `venom_waypoint`, `venom_nav_bt`, `venom_global_monitor`, and `venom_mission_manager` |
| System integration | `venom_bringup` | top-level bringup and robot assembly |
| Robot description | `venom_robot_description` | URDF, robot model, and TF publishing |
| Simulation | `venom_nav_simulation` | `MID360 + Gazebo + LIO + Nav2` validation workspace |

## Repository Layout

```text
venom_vnv/
├── driver/                          # driver layer
│   ├── livox_ros_driver2/
│   ├── ros2_hik_camera/
│   ├── scout_ros2/
│   ├── hunter_ros2/
│   ├── ugv_sdk/
│   ├── piper_ros/
│   ├── venom_px4_bridge/
│   └── venom_serial_driver/
├── perception/                      # perception layer
│   └── rm_auto_aim/
├── localization/                    # localization layer
│   ├── lio/
│   │   ├── Point-LIO/
│   │   ├── Fast-LIO/
│   │   └── rf2o_laser_odometry/
│   └── relocalization/
│       └── small_gicp_relocalization/
├── planning/                        # planning layer
│   ├── navigation/                  # navigation planners and controllers
│   └── manipulation/                # manipulation motion planning
├── mission/                         # mission layer
│   ├── navigation/                  # waypoint, BT, and monitoring
│   └── manipulation/                # manipulation-task flow
├── venom_bringup/                   # system layer: bringup and robot assembly
├── venom_robot_description/         # system layer: robot description and TF
├── simulation/
│   └── venom_nav_simulation/        # simulation layer
├── docs/                            # GitHub Pages docs
└── assets/                          # README / docs assets
```

## Quick Start

### Environment baseline

- Ubuntu 22.04
- ROS 2 Humble
- `rosdep`
- `colcon`
- Livox-SDK2

If ROS, `rosdep`, VS Code, or Livox-SDK2 are not ready yet, start from:

- [Environment Setup](https://venom-algorithm.github.io/Venom_VNV/en/environment)
- [LiDAR Setup](https://venom-algorithm.github.io/Venom_VNV/en/lidar_setup)

### Clone and build

If you already have an old workspace, go back to your home directory before removing it so the current shell does not stay inside a deleted path.

```bash
cd ~
rm -rf ~/venom_ws
mkdir -p ~/venom_ws/src
git clone --recurse-submodules https://github.com/Venom-Algorithm/Venom_VNV ~/venom_ws/src/venom_vnv

cp ~/venom_ws/src/venom_vnv/driver/livox_ros_driver2/package_ROS2.xml \
   ~/venom_ws/src/venom_vnv/driver/livox_ros_driver2/package.xml

cd ~/venom_ws
rosdep install -r --from-paths src --ignore-src --rosdistro $ROS_DISTRO -y
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release -DROS_EDITION=ROS2 -DHUMBLE_ROS=humble
```

If `rosdep` fails, try:

```bash
sudo rosdep init
rosdep update
```

## Common Launch Commands

```bash
cd ~/venom_ws
source install/setup.bash

# Mid360 + RViz validation
ros2 launch venom_bringup mid360_rviz.launch.py

# Mid360 + Point-LIO
ros2 launch venom_bringup mid360_point_lio.launch.py

# Infantry auto-aim pipeline
ros2 launch venom_bringup infantry_auto_aim.launch.py

# Scout Mini mapping
ros2 launch venom_bringup scout_mini_mapping.launch.py

# PX4 DDS probe
ros2 launch venom_bringup px4_agent_probe.launch.py
```

More commands:

- [Launch & Use](https://venom-algorithm.github.io/Venom_VNV/en/launch_usage)
- [Run Modes](https://venom-algorithm.github.io/Venom_VNV/en/run_modes)

## Documentation Guide

| Page | Description |
| --- | --- |
| [Quick Start](https://venom-algorithm.github.io/Venom_VNV/en/quick_start) | workspace initialization, dependency installation, and standard build flow |
| [Environment Setup](https://venom-algorithm.github.io/Venom_VNV/en/environment) | Ubuntu, ROS, rosdep, VS Code, and development-machine basics |
| [LiDAR Setup](https://venom-algorithm.github.io/Venom_VNV/en/lidar_setup) | MID360 networking, config files, and Livox-SDK2 |
| [Launch & Use](https://venom-algorithm.github.io/Venom_VNV/en/launch_usage) | common build, rebuild, and launch commands |
| [Modules & Interfaces](https://venom-algorithm.github.io/Venom_VNV/en/interface_reference) | entry point for drivers, perception, localization, planning, mission, system, and simulation |
| [Topic Reference](https://venom-algorithm.github.io/Venom_VNV/en/topics) | unified ROS 2 topic and message conventions |
| [TF Tree](https://venom-algorithm.github.io/Venom_VNV/en/tf_tree) | core frame and TF relationships |
| [Development Notes](https://venom-algorithm.github.io/Venom_VNV/en/development) | development environment, Git, fork / PR workflow, and submodule rules |

## Collaboration

Recommended collaboration flow:

```text
fork -> clone -> branch -> commit -> push -> Pull Request -> review -> merge
```

Current defaults:

- Chinese remains the default README
- English README and English docs are maintained alongside it
- code changes should preferably go through fork / PR
- submodule changes should be merged in the submodule first, then reflected in the main repository pointer

Details:

- [Development Notes](https://venom-algorithm.github.io/Venom_VNV/en/development)
- [Contributing](https://venom-algorithm.github.io/Venom_VNV/en/contributing)

## License

Each submodule keeps its own open-source license. Please refer to the `LICENSE` file inside the corresponding directory.
