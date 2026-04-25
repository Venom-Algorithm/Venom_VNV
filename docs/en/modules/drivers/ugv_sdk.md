---
title: UGV SDK
description: ugv_sdk — Low-level C++ SDK for AgileX / Weston Robot wheeled platforms.
---

## Module Role

`ugv_sdk` is not the ROS-facing entry point by itself. Instead, it is the low-level communication layer used by platform wrappers such as `scout_ros2` and `hunter_ros2`.

It handles:

- CAN communication
- protocol translation
- runtime robot abstraction
- helper scripts for CAN setup

## System Position

```text
scout_ros2 / hunter_ros2 -> ugv_sdk -> CAN -> chassis controller
```

## Common Helper Scripts

- `setup_can2usb.bash`
- `bringup_can2usb.bash`

## Recommended Reading

- [Scout Driver](scout_ros2.md)
- [Hunter Driver](hunter_ros2.md)
- [Chassis CAN Setup](../../deployment/chassis_can_setup.md)
