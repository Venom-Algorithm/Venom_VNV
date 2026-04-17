---
title: Architecture
permalink: /en/architecture
desc: Understand the four-layer structure of perception, localization, decision, and actuation.
breadcrumb: Modules & Interfaces
layout: default
---

## System View

Venom VNV can be understood as four large layers:

1. Perception
2. Localization
3. Decision / task orchestration
4. Actuation / robot interface

## Layer Responsibilities

| Layer | Responsibility |
| --- | --- |
| Perception | `perception/rm_auto_aim` and the camera-facing detection / tracking / solving pipeline |
| Localization | `localization/lio/*`, `localization/relocalization/*`, and map-alignment logic |
| Decision | Bringup composition, task logic, and robot-level mode switching |
| Actuation | Chassis, arm, serial controller, PX4 bridge, and low-level execution |

## Directory Mapping

| Layer | Main Directories | Description |
| --- | --- | --- |
| Perception | `driver/ros2_hik_camera` + `perception/rm_auto_aim` | Image input, detector, tracker, and solver |
| Localization | `driver/livox_ros_driver2` + `localization/lio` + `localization/relocalization` | LiDAR input, LIO, odometry, and relocalization |
| Decision | `venom_bringup` | Launch composition, mode switching, and task control |
| Actuation | `driver/scout_ros2`, `driver/hunter_ros2`, `driver/piper_ros`, `driver/venom_serial_driver`, `driver/venom_px4_bridge` | Robot-facing control and bridge interfaces |

## Simulation Side Project

The repository now also carries a standalone simulation workspace:

- `simulation/venom_nav_simulation`

It is used for:

- `MID360 + Gazebo + LIO + Nav2` integration testing
- regression-oriented workflow validation
- validating localization and navigation pipelines before touching hardware

## Why This Structure Matters

The project tries to keep the layers reusable across robot forms. That is why the documentation emphasizes:

- Stable ROS 2 topics
- Stable TF names
- Clear package boundaries
- Bringup-level composition instead of hard coupling
