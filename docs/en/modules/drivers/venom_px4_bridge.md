---
title: PX4 Bridge
description: venom_px4_bridge — PX4 integration project root, with vendored px4_msgs
  and the VNV bridge package.
---

## Module Role

`driver/venom_px4_bridge` is not a single ROS package. It is the PX4 integration project root inside VNV.

It currently contains:

- `px4_msgs/`: vendored PX4 ROS 2 message definitions
- `venom_px4_bridge/`: the VNV-owned bridge package

The goal is to keep PX4 message pinning, DDS probing, and state translation inside the bridge layer instead of leaking raw PX4 details upward.

## Current Scope

The first slice currently includes:

- `px4_agent_monitor`
- `px4_status_adapter`
- `px4_external_pose_bridge`
- `px4_agent_probe.launch.py`
- `px4_external_pose_bridge.launch.py`

Current bridge outputs:

- `/px4_bridge/agent_status`
- `/px4_bridge/state`
- `/px4_bridge/odom`
- `/px4_bridge/health`
- `/fmu/in/vehicle_visual_odometry`

## Recommended Entry

For a basic DDS Agent and PX4 link check:

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch venom_bringup px4_agent_probe.launch.py
```

For a focused build of PX4-related packages:

```bash
source /opt/ros/humble/setup.bash
cd ~/venom_ws
colcon build --symlink-install --packages-up-to px4_msgs venom_px4_bridge venom_bringup
```

## External Pose Bridge

`px4_external_pose_bridge` converts upper-layer `nav_msgs/Odometry` from LIO / VPS algorithms into PX4-facing `px4_msgs/VehicleOdometry`.

Default data flow:

```text
/lio/vps/odometry
  -> px4_external_pose_bridge
  -> /fmu/in/vehicle_visual_odometry
  -> PX4 EKF2 external vision / visual odometry fusion
```

Default entry point in the main workspace:

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch venom_bringup px4_vps_bridge.launch.py
```

Common launch arguments:

| Argument | Meaning | Default |
| --- | --- | --- |
| `fmu_prefix` | PX4 DDS topic namespace prefix. | `"/fmu"` |
| `input_odom_topic` | Upstream LIO / VPS `nav_msgs/Odometry` topic. | `"/lio/vps/odometry"` |

Override `input_odom_topic` when the upstream localization output uses another topic:

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch venom_bringup px4_vps_bridge.launch.py input_odom_topic:=/lio/odom
```

PX4-side fusion still depends on EKF2 parameters, timestamps, frames, and covariance settings.

## Why This Is a Project Root

This layout isolates:

1. upstream `px4_msgs` version changes
2. DDS Agent probing and availability checks
3. VNV-owned bridge interfaces

Upper layers should depend on the bridge-facing outputs, not raw PX4 topic details.

## Related Pages

- [Drivers](index.md)
- [System Bringup](../integration/venom_bringup.md)
- [Launch & Use](../../home/launch_usage.md)

## Further Reading

- [venom_px4_bridge README](https://github.com/Venom-Algorithm/Venom_VNV/blob/master/driver/venom_px4_bridge/README.md)
- [deployment.md](https://github.com/Venom-Algorithm/Venom_VNV/blob/master/driver/venom_px4_bridge/docs/deployment.md)
- [COMPATIBILITY.md](https://github.com/Venom-Algorithm/Venom_VNV/blob/master/driver/venom_px4_bridge/COMPATIBILITY.md)
