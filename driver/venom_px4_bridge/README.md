# venom_px4_bridge Project

This directory is the PX4 integration project root inside VNV.

It is intentionally not a ROS package itself.

It contains two ROS packages:

- `px4_msgs/`: vendored official PX4 ROS 2 message definitions
- `venom_px4_bridge/`: VNV-owned PX4 bridge package

## Layout

```text
driver/venom_px4_bridge/
  README.md
  COMPATIBILITY.md
  docs/
    deployment.md
  px4_msgs/
    package.xml
    CMakeLists.txt
    msg/
    srv/
  venom_px4_bridge/
    package.xml
    CMakeLists.txt
    include/
    src/
    launch/
    config/
```

## Why This Exists

PX4 integration is not treated as a normal device driver in VNV.

This project isolates:

- PX4 ROS 2 message version pinning
- DDS topic and agent probing
- PX4-native state translation
- future offboard and external-pose adapters

Upper-layer bringup should depend on the bridge package interfaces, not raw `/fmu/*` details.

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

## Build

From the workspace root:

```bash
source /opt/ros/humble/setup.bash
colcon build --symlink-install --packages-up-to px4_msgs venom_px4_bridge venom_bringup
```

## Docs

- Compatibility matrix: [`COMPATIBILITY.md`](./COMPATIBILITY.md)
- Deployment guide: [`docs/deployment.md`](./docs/deployment.md)

## Upstream Source Of `px4_msgs`

The vendored `px4_msgs` content comes from:

- upstream: <https://github.com/PX4/px4_msgs>
- branch line: `release/1.16`
- upstream base commit: `392e831c1f659429ca83902e66820d7094591410`
