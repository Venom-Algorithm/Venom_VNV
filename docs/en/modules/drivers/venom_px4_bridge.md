---
title: PX4 Bridge
permalink: /en/venom_px4_bridge
desc: venom_px4_bridge — PX4 integration project root, with vendored px4_msgs and the VNV bridge package.
breadcrumb: Drivers
layout: default
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
- `px4_agent_probe.launch.py`

Current bridge outputs:

- `/px4_bridge/agent_status`
- `/px4_bridge/state`
- `/px4_bridge/odom`
- `/px4_bridge/health`

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

## Why This Is a Project Root

This layout isolates:

1. upstream `px4_msgs` version changes
2. DDS Agent probing and availability checks
3. VNV-owned bridge interfaces

Upper layers should depend on the bridge-facing outputs, not raw PX4 topic details.

## Related Pages

- [Drivers]({{ '/en/driver_overview' | relative_url }})
- [System Bringup]({{ '/en/venom_bringup' | relative_url }})

## Further Reading

- [venom_px4_bridge README](/Users/liyh/venom_vnv/driver/venom_px4_bridge/README.md)
- [deployment.md](/Users/liyh/venom_vnv/driver/venom_px4_bridge/docs/deployment.md)
- [COMPATIBILITY.md](/Users/liyh/venom_vnv/driver/venom_px4_bridge/COMPATIBILITY.md)
