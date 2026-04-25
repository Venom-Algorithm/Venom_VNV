---
title: Drivers
description: Responsibilities, interfaces, and dependencies of the hardware-facing
  packages.
---

## Module Groups

- [Livox LiDAR Driver](livox_ros_driver2.md)
- [Hikrobot Camera Driver](ros2_hik_camera.md)
- [Chassis Driver Overview](chassis_driver.md)
- [Scout Driver](scout_ros2.md)
- [Hunter Driver](hunter_ros2.md)
- [UGV SDK](ugv_sdk.md)
- [Piper Arm Driver](piper_ros.md)
- [PX4 Bridge](venom_px4_bridge.md)
- [Serial Driver](venom_serial_driver.md)

## Covered Driver Packages

| Category | Package | Doc | Description |
| --- | --- | --- | --- |
| LiDAR | `livox_ros_driver2` | [Livox LiDAR Driver](livox_ros_driver2.md) | MID360 point cloud and IMU input |
| Camera | `ros2_hik_camera` | [Hikrobot Camera Driver](ros2_hik_camera.md) | Image and camera-info input |
| Chassis | `scout_ros2` | [Scout Driver](scout_ros2.md) | ROS 2 wrapper for Scout platforms |
| Chassis | `hunter_ros2` | [Hunter Driver](hunter_ros2.md) | ROS 2 wrapper for Hunter platforms |
| Chassis | `ugv_sdk` | [UGV SDK](ugv_sdk.md) | Low-level SDK, CAN abstraction, and tooling |
| Arm | `piper_ros` | [Piper Arm Driver](piper_ros.md) | Arm control, URDF, MoveIt, and simulation packages |
| Flight bridge | `venom_px4_bridge` | [PX4 Bridge](venom_px4_bridge.md) | PX4 ROS 2 messages, DDS probing, and bridge state outputs |
| Serial | `venom_serial_driver` | [Serial Driver](venom_serial_driver.md) | Controller communication bridge |

## What Every Driver Page Should Answer

1. Which hardware or SDK it depends on
2. How it is launched
3. Which topics it publishes or subscribes to
4. What role it plays in the full robot stack

## Position in the System

The driver layer is the boundary between physical devices and ROS 2 modules. It is the entry point for upper-layer algorithms.
