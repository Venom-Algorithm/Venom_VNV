---
title: Deployment & Usage
description: Entry point for environment setup, hardware configuration, run modes,
  and system-level interfaces.
---

## Reading Order

This section is for first deployment and on-site integration. Read it in this order:

1. [Environment Setup](environment.md): prepare Ubuntu, ROS 2 Humble, rosdep, VS Code, remote desktop, and common development tools
2. [LiDAR Setup](lidar_setup.md): install Livox-SDK2, configure MID360 static IP and parameters, and verify the link
3. [Launch & Use](../home/launch_usage.md): common build, rebuild, test launch, and robot startup commands

## Hardware Links

- [RealSense Setup](realsense_setup.md): D435i / RealSense SDK and ROS wrapper setup
- [Chassis CAN Setup](chassis_can_setup.md): CAN adapter setup for Scout / Hunter platforms
- [Arm CAN Setup](piper_can_setup.md): Piper CAN device identification, naming, and pre-start checks
- [rc.local](rc_local.md): boot-time startup, static routes, and network priority

## Runtime & Interfaces

- [Run Modes](run_modes.md): usage patterns for different integration, test, and full-system modes
- [Topics & TF Overview](system_overview.md): system-level topics and core TF conventions

For package-level interfaces and parameters, continue with [Modules & Interfaces](../modules/index.md).
