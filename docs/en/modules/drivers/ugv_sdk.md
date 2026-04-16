---
title: UGV SDK
permalink: /en/ugv_sdk
desc: ugv_sdk — Low-level C++ SDK for AgileX / Weston Robot wheeled platforms.
breadcrumb: Drivers
layout: default
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

- [Scout Driver]({{ '/en/scout_ros2' | relative_url }})
- [Hunter Driver]({{ '/en/hunter_ros2' | relative_url }})
- [Chassis CAN Setup]({{ '/en/chassis_can_setup' | relative_url }})
