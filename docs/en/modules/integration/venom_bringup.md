---
title: System Bringup
description: venom_bringup — System launch composition and task-control framework.
---

## Module Role

`venom_bringup` is the repository-level system-layer entry. It is responsible for:

- launch composition
- mode selection
- task-control entry points
- robot-level configuration dispatch

## Common Launch Entries

- `camera.launch.py`
- `mid360_rviz.launch.py`
- `mid360_point_lio.launch.py`
- `d435i_test.launch.py`
- `infantry_auto_aim.launch.py`
- `scout_mini_mapping.launch.py`
- `sentry_mapping.launch.py`
- `relocalization_bringup.launch.py`
- `px4_agent_probe.launch.py`
- `px4_vps_bridge.launch.py`
- `robot_bringup.launch.py`

## Related Pages

- [Launch & Use](../../home/launch_usage.md)
- [Run Modes](../../deployment/run_modes.md)

## Note

The Chinese page remains the more detailed source for configuration and task-controller notes.
