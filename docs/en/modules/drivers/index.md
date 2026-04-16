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
- [Serial Driver]({{ '/en/venom_serial_driver' | relative_url }})

## What Every Driver Page Should Answer

1. Which hardware or SDK it depends on
2. How it is launched
3. Which topics it publishes or subscribes to
4. What role it plays in the full robot stack

## Position in the System

The driver layer is the boundary between physical devices and ROS 2 modules. It is the entry point for upper-layer algorithms.
