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

Single packages answer “how one module runs.” `venom_bringup` answers “how the full robot stack is composed.”

Architecturally, new waypoint, behavior-tree, monitor, and task-dispatch packages should move toward the `mission/` layer. The mission-control code that already exists today is still maintained inside `venom_bringup` as a transitional implementation.

## Common Launch Entries

| Launch file | Source path | Role |
| --- | --- | --- |
| `camera.launch.py` | `launch/camera.launch.py` | standalone camera validation |
| `mid360_rviz.launch.py` | `launch/examples/mid360_rviz.launch.py` | MID360 driver and RViz validation |
| `mid360_point_lio.launch.py` | `launch/examples/mid360_point_lio.launch.py` | MID360 + Point-LIO integration |
| `mid360_point_lio_odom.launch.py` | `launch/examples/mid360_point_lio_odom.launch.py` | MID360 + Point-LIO odom-only mode |
| `mid360_point_lio_async_map.launch.py` | `launch/examples/mid360_point_lio_async_map.launch.py` | MID360 + Point-LIO explicit async-map mode |
| `mid360_point_lio_offline_map.launch.py` | `launch/examples/mid360_point_lio_offline_map.launch.py` | Point-LIO offline mapping |
| `mid360_record_raw.launch.py` | `launch/examples/mid360_record_raw.launch.py` | raw MID360 bag recording |
| `d435i_test.launch.py` | `launch/examples/d435i_test.launch.py` | RealSense D435i validation |
| `px4_agent_probe.launch.py` | `launch/examples/px4_agent_probe.launch.py` | PX4 DDS Agent probe |
| `px4_vps_bridge.launch.py` | `launch/examples/px4_vps_bridge.launch.py` | PX4 external-pose / VPS odometry bridge |
| `infantry_auto_aim.launch.py` | `launch/infantry/infantry_auto_aim.launch.py` | infantry auto-aim stack |
| `sentry_mapping.launch.py` | `launch/sentry/sentry_mapping.launch.py` | sentry mapping integration |
| `sentry_navigation.launch.py` | `launch/sentry/sentry_navigation.launch.py` | sentry navigation integration |
| `scout_mini_mapping.launch.py` | `launch/scout_mini/scout_mini_mapping.launch.py` | Scout Mini mapping and navigation integration |
| `relocalization_bringup.launch.py` | `launch/relocalization_bringup.launch.py` | historical GICP relocalization entry, currently disabled |
| `health_aware_navigation.launch.py` | `launch/health_aware_navigation.launch.py` | health-aware mission-control mode |
| `robot_bringup.launch.py` | `launch/robot_bringup.launch.py` | robot-type selector template, not the preferred daily entry yet |

Use only the launch filename in `ros2 launch`, for example `ros2 launch venom_bringup mid360_rviz.launch.py`. Do not include source subdirectories such as `examples/`, `sentry/`, or `scout_mini/` in the command.

`robot_bringup.launch.py` already contains `robot_type` selection logic, but the included per-robot templates such as `scout_mini/robot_bringup.launch.py`, `sentry/robot_bringup.launch.py`, `hunter_se/robot_bringup.launch.py`, and `infantry/robot_bringup.launch.py` are not all present yet. Use the concrete launch files above for daily integration.

## Configuration Entrypoints

`venom_bringup` does not keep every parameter in one yaml file. It dispatches configuration by robot and subsystem:

- robot-specific configs: `config/scout_mini/`, `config/sentry/`, `config/infantry/`
- camera params: `config/*/camera_params.yaml`
- auto-aim params: `config/*/node_params.yaml`
- serial params: `config/*/serial_params.yaml`
- LIO passthrough params: `config/*/point_lio_mapping.yaml`, `config/examples/point_lio_online_odom.yaml`, `config/examples/point_lio_online_async_map.yaml`, `config/examples/point_lio_offline_map.yaml`
- navigation params: `config/*/nav2_params.yaml`
- mission-control params: `mission_config.yaml`, `waypoints.yaml`

## Mission Controller

The current mission-control implementation under `venom_bringup` provides:

- state monitoring
- pause / recovery / retry behavior triggers
- mission-state persistence and recovery

Main files:

- [`multi_waypoint_commander.py`](https://github.com/Venom-Algorithm/Venom_VNV/blob/master/venom_bringup/venom_bringup/multi_waypoint_commander.py)
- [`health_aware_commander.py`](https://github.com/Venom-Algorithm/Venom_VNV/blob/master/venom_bringup/venom_bringup/health_aware_commander.py)
- [`mission_controller/`](https://github.com/Venom-Algorithm/Venom_VNV/tree/master/venom_bringup/venom_bringup/mission_controller)
- [`plugins/`](https://github.com/Venom-Algorithm/Venom_VNV/tree/master/venom_bringup/venom_bringup/plugins)
- [`mission_config.yaml`](https://github.com/Venom-Algorithm/Venom_VNV/blob/master/venom_bringup/config/scout_mini/mission_config.yaml)
- [`waypoints.yaml`](https://github.com/Venom-Algorithm/Venom_VNV/blob/master/venom_bringup/config/scout_mini/waypoints.yaml)

The two key runtime parameters are:

| Parameter | Role | Default meaning |
| --- | --- | --- |
| `waypoints_file` | waypoint yaml path | current robot waypoint config |
| `mission_config_file` | mission config yaml path | current robot mission-control config |

## Recommended Usage

Prefer concrete `venom_bringup` entries for daily work:

```bash
ros2 launch venom_bringup mid360_point_lio.launch.py
ros2 launch venom_bringup infantry_auto_aim.launch.py
ros2 launch venom_bringup health_aware_navigation.launch.py
```

Treat `robot_bringup.launch.py` as a top-level template until all per-robot bringup files are completed.

## Related Pages

- [Launch & Use](../../home/launch_usage.md)
- [Run Modes](../../deployment/run_modes.md)
