---
title: Troubleshooting
description: A practical entry point for debugging by subsystem.
---

## Recommended Order

When something does not work, debug from bottom to top:

1. hardware link
2. driver output
3. localization / perception output
4. integrated bringup behavior

## By Subsystem

- LiDAR issues: start from [LiDAR Setup](../deployment/lidar_setup.md)
- Chassis CAN issues: start from [Chassis CAN Setup](../deployment/chassis_can_setup.md)
- Arm CAN issues: start from [Arm CAN Setup](../deployment/piper_can_setup.md)
- Bringup issues: start from [System Bringup](../modules/integration/venom_bringup.md)

## Principle

Avoid debugging the whole robot stack first. Validate the lowest broken layer and move upward.
