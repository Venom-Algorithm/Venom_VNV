---
title: Navigation Simulation Workspace
description: venom_nav_simulation — Standalone workspace for MID360, Gazebo, LIO,
  and Nav2 validation.
---

## Module Role

`simulation/venom_nav_simulation` is a standalone ROS 2 simulation workspace used for:

- simulated MID-360 and IMU streams
- `Point-LIO` / `Fast-LIO` validation
- `Nav2` workflow testing
- localization and navigation verification before touching real hardware

## Main Capabilities

- Gazebo-based vehicle simulation
- simulated MID-360 point cloud output
- simulated IMU output
- `Point-LIO` / `Fast-LIO` integration
- `Nav2` mapping and navigation validation

## Current Layout

```text
simulation/venom_nav_simulation/
├── src/rm_nav_bringup
├── src/rm_navigation
├── src/rm_localization
├── src/rm_perception
└── src/rm_simulation/venom_mid360_simulation
```

## Quick Start

```bash
cd simulation/venom_nav_simulation
rosdep install -r --from-paths src --ignore-src --rosdistro $ROS_DISTRO -y
colcon build --symlink-install
source install/setup.bash
ros2 launch rm_nav_bringup bringup_sim.launch.py \
  world:=RMUL \
  mode:=nav \
  lio:=pointlio \
  localization:=slam_toolbox \
  lio_rviz:=False \
  nav_rviz:=True
```

## Docker Path

If you want to use the root-level unified sim environment:

```bash
cd ~/venom_ws/src/venom_vnv
make build
make up
make shell
```

Inside the container:

```bash
cd /ros_ws
source /opt/ros/humble/setup.bash
rosdep install -r --from-paths src --ignore-src --rosdistro humble -y
colcon build --cmake-args -DCMAKE_BUILD_TYPE=Release -DROS_EDITION=ROS2 -DHUMBLE_ROS=humble
```

Or use the wrapped commands:

```bash
cd ~/venom_ws/src/venom_vnv
make rosdep
make colcon
```

To reproduce the CI build locally:

```bash
cd ~/venom_ws/src/venom_vnv
make ci-build
```

The current Docker image is based on `ros:humble-ros-base` and includes Ignition Fortress, Nav2, RViz2, PCL, OpenCV, and YOLO runtime dependencies. CI skips hardware drivers and Gazebo Classic packages.

## Why It Stays Separate

This is not meant to be merged into the main deployment workspace:

- dependencies are heavier
- simulation assets are larger
- simulation launch composition differs from real-robot bringup

It is better treated as a simulation baseline.

## Related Pages

- [Simulation](index.md)
- [Localization](../localization/index.md)
- [Planning](../planning/index.md)
