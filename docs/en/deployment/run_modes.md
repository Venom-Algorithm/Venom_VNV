---
title: Run Modes
description: Typical bringup combinations and when each mode should be used.
---

## Purpose

The repository is not used in just one runtime shape. Depending on hardware availability and the current task, you may only want:

- A single driver validation flow
- A localization-only flow
- An auto aim test flow
- A mapping or relocalization flow
- A full system bringup

## Common Patterns

| Mode | Focus |
| --- | --- |
| Driver validation | Check LiDAR, camera, CAN, or serial links separately |
| Localization test | Run MID360 + Point-LIO / Fast-LIO without the rest of the stack |
| Point-LIO odom-only | Keep realtime odometry and TF output while disabling map publication and PCD saving load |
| Point-LIO async map | Keep odometry realtime and move map publication / PCD-related work to the async map worker |
| Point-LIO offline mapping | Read rosbag2 offline and export a PCD map |
| Auto aim test | Focus on camera, detector, tracker, and solver |
| Mapping | Validate localization and mapping outputs |
| Relocalization | Validate global localization against an existing map |
| PX4 external-pose bridge | Convert upstream `nav_msgs/Odometry` into PX4 `VehicleOdometry` |
| Mission control | Run health-aware multi-waypoint navigation |
| Full robot bringup | Start the integrated stack through `venom_bringup` |

## Current Entrypoints

| Mode | Entry |
| --- | --- |
| MID360 RViz validation | `mid360_rviz.launch.py` |
| MID360 + Point-LIO | `mid360_point_lio.launch.py` |
| MID360 + Point-LIO odom-only | `mid360_point_lio_odom.launch.py` |
| MID360 + Point-LIO async map | `mid360_point_lio_async_map.launch.py` |
| Point-LIO offline mapping | `mid360_point_lio_offline_map.launch.py` |
| D435i validation | `d435i_test.launch.py` |
| PX4 DDS probe | `px4_agent_probe.launch.py` |
| PX4 external-pose bridge | `px4_vps_bridge.launch.py` |
| Health-aware mission control | `health_aware_navigation.launch.py` |
| Scout Mini mapping | `scout_mini_mapping.launch.py` |
| Sentry mapping | `sentry_mapping.launch.py` |
| Relocalization | `relocalization_bringup.launch.py` |
| Top-level robot selector | `robot_bringup.launch.py`, currently a template entry rather than the preferred daily launch |

## Recommendation

For day-to-day work, do not jump into a full bringup first. A safer order is:

1. Validate drivers
2. Validate localization
3. Validate task-specific modules
4. Move to integrated bringup last

## Related Pages

- [Launch & Use](../home/launch_usage.md)
- [System Bringup](../modules/integration/venom_bringup.md)
