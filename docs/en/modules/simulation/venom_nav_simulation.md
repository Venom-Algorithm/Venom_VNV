---
title: Navigation Simulation Workspace
permalink: /en/venom_nav_simulation
desc: venom_nav_simulation — Standalone workspace for MID360, Gazebo, LIO, and Nav2 validation.
breadcrumb: Simulation
layout: default
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

## Why It Stays Separate

This is not meant to be merged into the main deployment workspace:

- dependencies are heavier
- simulation assets are larger
- simulation launch composition differs from real-robot bringup

It is better treated as a simulation baseline.

## Related Pages

- [Simulation]({{ '/en/simulation_overview' | relative_url }})
- [Localization]({{ '/en/localization_overview' | relative_url }})
- [Planning]({{ '/en/planning_overview' | relative_url }})
