---
title: Drivers
permalink: /en/driver_overview
desc: Responsibilities, interfaces, and dependencies of the hardware-facing packages.
breadcrumb: Modules & Interfaces
layout: default
---

## Module Groups

- [Livox LiDAR Driver]({{ '/en/livox_ros_driver2' | relative_url }})
- [Hikrobot Camera Driver]({{ '/en/ros2_hik_camera' | relative_url }})
- [Chassis Driver Overview]({{ '/en/chassis_driver' | relative_url }})
- [Scout Driver]({{ '/en/scout_ros2' | relative_url }})
- [Hunter Driver]({{ '/en/hunter_ros2' | relative_url }})
- [UGV SDK]({{ '/en/ugv_sdk' | relative_url }})
- [Piper Arm Driver]({{ '/en/piper_ros' | relative_url }})
- [PX4 Bridge]({{ '/en/venom_px4_bridge' | relative_url }})
- [Serial Driver]({{ '/en/venom_serial_driver' | relative_url }})

## Covered Driver Packages

| Category | Package | Doc | Description |
| --- | --- | --- | --- |
| LiDAR | `livox_ros_driver2` | [Livox LiDAR Driver]({{ '/en/livox_ros_driver2' | relative_url }}) | MID360 point cloud and IMU input |
| Camera | `ros2_hik_camera` | [Hikrobot Camera Driver]({{ '/en/ros2_hik_camera' | relative_url }}) | Image and camera-info input |
| Chassis | `scout_ros2` | [Scout Driver]({{ '/en/scout_ros2' | relative_url }}) | ROS 2 wrapper for Scout platforms |
| Chassis | `hunter_ros2` | [Hunter Driver]({{ '/en/hunter_ros2' | relative_url }}) | ROS 2 wrapper for Hunter platforms |
| Chassis | `ugv_sdk` | [UGV SDK]({{ '/en/ugv_sdk' | relative_url }}) | Low-level SDK, CAN abstraction, and tooling |
| Arm | `piper_ros` | [Piper Arm Driver]({{ '/en/piper_ros' | relative_url }}) | Arm control, URDF, MoveIt, and simulation packages |
| Flight bridge | `venom_px4_bridge` | [PX4 Bridge]({{ '/en/venom_px4_bridge' | relative_url }}) | PX4 ROS 2 messages, DDS probing, and bridge state outputs |
| Serial | `venom_serial_driver` | [Serial Driver]({{ '/en/venom_serial_driver' | relative_url }}) | Controller communication bridge |

## What Every Driver Page Should Answer

1. Which hardware or SDK it depends on
2. How it is launched
3. Which topics it publishes or subscribes to
4. What role it plays in the full robot stack

## Position in the System

The driver layer is the boundary between physical devices and ROS 2 modules. It is the entry point for upper-layer algorithms.
