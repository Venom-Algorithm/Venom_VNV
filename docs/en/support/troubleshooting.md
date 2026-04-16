---
title: Troubleshooting
permalink: /en/troubleshooting
desc: A practical entry point for debugging by subsystem.
breadcrumb: Support & Community
layout: default
---

## Recommended Order

When something does not work, debug from bottom to top:

1. hardware link
2. driver output
3. localization / perception output
4. integrated bringup behavior

## By Subsystem

- LiDAR issues: start from [LiDAR Setup]({{ '/en/lidar_setup' | relative_url }})
- Chassis CAN issues: start from [Chassis CAN Setup]({{ '/en/chassis_can_setup' | relative_url }})
- Arm CAN issues: start from [Arm CAN Setup]({{ '/en/piper_can_setup' | relative_url }})
- Bringup issues: start from [System Bringup]({{ '/en/venom_bringup' | relative_url }})

## Principle

Avoid debugging the whole robot stack first. Validate the lowest broken layer and move upward.
