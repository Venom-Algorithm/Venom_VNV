# PX4 Bridge Deployment Plan

Date: 2026-04-17
Workspace: `/Users/liyh/venom_vnv`
Reference project: `/tmp/Sunray`

## Scope

This document fixes the first PX4 integration baseline for VNV and records the repository changes needed to make it deployable.

The target is not "just add a driver".

The target is:

- make PX4 DDS connectivity verifiable inside VNV
- keep PX4-specific protocol details out of upper-layer bringup logic
- prepare a thin bridge package that can later own offboard sequencing and external pose injection

## Official References

Primary references used for this plan:

- PX4 ROS 2 User Guide: <https://docs.px4.io/main/zh/ros2/user_guide>
- PX4 uXRCE-DDS middleware guide: <https://docs.px4.io/main/en/middleware/uxrce_dds>
- Official `px4_msgs` repository: <https://github.com/PX4/px4_msgs>
- Official `px4_ros_com` repository: <https://github.com/PX4/px4_ros_com>

Open-source architecture reference used for layering only:

- Sunray: `/tmp/Sunray` at commit `80afee5`

## Fixed Baseline

The baseline chosen for VNV v1 is:

- Ubuntu `22.04`
- ROS 2 `Humble`
- PX4 firmware line `v1.16.x`
- `px4_msgs` branch `release/1.16`
- pinned `px4_msgs` commit `392e831c1f659429ca83902e66820d7094591410`
- `Micro XRCE-DDS Agent` version `v2.4.3`

Why this matters:

- PX4 ROS 2 messages must match the firmware release line
- PX4 official docs explicitly describe the bridge around `uxrce_dds_client` + agent + `px4_msgs`
- from PX4 `v1.16`, the official docs also describe message versioning and the optional translation-node path for cross-version operation
- VNV should avoid that extra compatibility layer in v1 and instead pin one clean version line

## What Was Added To VNV

### 1. `driver/px4_msgs`

Added as a workspace submodule on branch `release/1.16`.

Purpose:

- provide the official ROS 2 interface definitions generated from PX4 uORB topics
- make `venom_px4_bridge` build against a pinned PX4 release line

### 2. `driver/venom_px4_bridge`

Added as a new `ament_cmake` package.

Current first-version nodes:

- `px4_status_adapter`
- `px4_agent_monitor`

Current first-version launch/config:

- `driver/venom_px4_bridge/launch/px4_agent_probe.launch.py`
- `driver/venom_px4_bridge/config/px4_bridge.yaml`

Current first-version outputs:

- `/px4_bridge/state`
- `/px4_bridge/odom`
- `/px4_bridge/health`
- `/px4_bridge/agent_status`

### 3. `venom_bringup` example entry

Added:

- `venom_bringup/launch/examples/px4_agent_probe.launch.py`

Purpose:

- give VNV a workspace-native PX4 probe entrypoint
- keep PX4 startup out of the generic top-level robot bringup until the interface is stable

## Why PX4 Is Not Treated As A Normal Driver

A normal driver mostly solves device I/O plus launch parameters.

PX4 integration also needs to solve:

- DDS transport and agent process management
- PX4 message version matching
- offboard keepalive and command sequencing
- arming and mode transition safety
- NED/FRD to ENU/FLU frame conversion
- external pose injection rules
- firmware-facing topic naming and QoS behavior

So the correct VNV split is:

- bringup owns parameters, namespaces, transport selection, startup order
- `venom_px4_bridge` owns PX4-native protocol and state translation
- upper layers talk to bridge outputs, not raw `/fmu/*`

## Why `px4_ros_com` Is Reference Material, Not The VNV Core Dependency

`px4_ros_com` is useful for:

- official examples
- offboard example patterns
- translation-node reference for mixed message versions

But it is not the right top-level abstraction for VNV because:

- VNV still needs its own stable internal interface
- VNV still needs its own bringup conventions and state packaging
- VNV should avoid leaking PX4-native topic details into mission/controller layers

So the VNV shape should be:

- depend on `px4_msgs`
- own a thin bridge package
- use `px4_ros_com` only as reference when adding later offboard/external-pose flows

## What Sunray Contributed

Sunray is ROS 1 + MAVROS, so it should not be copied literally.

Its value is the architecture split:

- connectivity layer
- external pose bridge
- packaged vehicle state
- control/mode state machine
- upper layers using abstract UAV commands instead of raw middleware topics

That maps into VNV as:

- `px4_agent_monitor`
- `px4_status_adapter`
- later `px4_external_pose_bridge`
- later `px4_mode_manager`
- later `px4_command_adapter`

## Current First-Version Behavior

### `px4_status_adapter`

Responsibilities:

- subscribe to selected `/fmu/out/*` topics
- convert PX4 `VehicleOdometry` from NED/FRD into ROS ENU/FLU
- publish ROS-standard odometry for the rest of VNV
- publish a compact bridge state summary
- publish diagnostic health information

Topics consumed now:

- `/fmu/out/vehicle_status`
- `/fmu/out/vehicle_odometry`
- `/fmu/out/battery_status`
- `/fmu/out/vehicle_control_mode`
- `/fmu/out/failsafe_flags`
- `/fmu/out/timesync_status`

Topics produced now:

- `/px4_bridge/state`
- `/px4_bridge/odom`
- `/px4_bridge/health`

### `px4_agent_monitor`

Responsibilities:

- check that required PX4 DDS topics exist
- subscribe to `TimesyncStatus` to confirm the DDS path is live
- publish diagnostics that make bringup failures obvious

Topic produced now:

- `/px4_bridge/agent_status`

### `px4_agent_probe.launch.py`

Responsibilities:

- optionally start `MicroXRCEAgent`
- start `px4_agent_monitor`
- start `px4_status_adapter`

Supported transport automation in the launch file now:

- `udp4`
- `serial`

## Complete Deployment Sequence

### Step 1. Clone VNV With Submodules

```bash
git clone --recurse-submodules <your-vnv-remote> ~/venom_ws/src/venom_vnv
```

If the workspace already exists:

```bash
cd ~/venom_ws/src/venom_vnv
git submodule update --init --recursive
```

### Step 2. Install ROS 2 Base Dependencies

This repository assumes ROS 2 Humble on Ubuntu 22.04.

Example:

```bash
sudo apt update
rosdep update
cd ~/venom_ws
rosdep install -r --from-paths src --ignore-src --rosdistro humble -y
```

### Step 3. Install `Micro XRCE-DDS Agent`

PX4 official middleware docs require the agent on the companion side.

Recommended path is the official source build pinned to `v2.4.3`:

```bash
cd /tmp
git clone https://github.com/eProsima/Micro-XRCE-DDS-Agent.git
cd Micro-XRCE-DDS-Agent
git checkout v2.4.3
mkdir -p build
cd build
cmake ..
make -j$(nproc)
sudo make install
sudo ldconfig
```

Expected command after installation:

```bash
MicroXRCEAgent udp4 -p 8888
```

### Step 4. Build The VNV PX4 Slice

```bash
cd ~/venom_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install --packages-up-to px4_msgs venom_px4_bridge venom_bringup
source install/setup.bash
```

### Step 5. Bring Up PX4 SITL First

Start PX4 SITL using the official PX4 workflow for the chosen firmware line.

Important rule:

- PX4 must already have `uxrce_dds_client` active and using the same transport as the companion-side agent

For the default VNV probe path, use UDP and port `8888`.

### Step 6. Run The VNV PX4 Probe

From the workspace:

```bash
source /opt/ros/humble/setup.bash
source ~/venom_ws/install/setup.bash
ros2 launch venom_bringup px4_agent_probe.launch.py
```

This example defaults to:

- `start_agent:=true`
- `agent_transport:=udp4`
- `agent_port:=8888`

If the agent is managed elsewhere:

```bash
ros2 launch venom_bringup px4_agent_probe.launch.py start_agent:=false
```

If the PX4 companion link uses serial:

```bash
ros2 launch venom_bringup px4_agent_probe.launch.py \
  agent_transport:=serial \
  agent_device:=/dev/ttyUSB0 \
  agent_baudrate:=921600
```

### Step 7. Verify The DDS Path

Minimum checks:

```bash
ros2 topic list | grep '^/fmu/'
ros2 topic echo /px4_bridge/agent_status
ros2 topic echo /px4_bridge/health
ros2 topic echo /px4_bridge/state
ros2 topic echo /px4_bridge/odom
```

You should see:

- `/fmu/out/vehicle_status`
- `/fmu/out/vehicle_odometry`
- `/fmu/out/timesync_status`
- `/px4_bridge/agent_status`
- `/px4_bridge/health`
- `/px4_bridge/state`
- `/px4_bridge/odom`

## Real-Hardware Checklist

Before trying offboard or external pose on hardware, confirm all of these first:

1. PX4 firmware line is `v1.16.x`
2. `driver/px4_msgs` is still pinned to `release/1.16`
3. companion-side `MicroXRCEAgent` transport matches PX4 `uxrce_dds_client`
4. PX4 parameter `UXRCE_DDS_CFG` is set so the client actually runs with the expected transport
5. topic namespace is really `/fmu` and not remapped by firmware configuration
6. the bridge sees `TimesyncStatus` continuously, not only once
7. frame usage downstream assumes ROS ENU/FLU, not PX4 NED/FRD

## What Is Still Intentionally Deferred

These are not implemented yet and should be added in this order:

1. `px4_mode_manager`
2. `px4_command_adapter`
3. `px4_offboard_test.launch.py`
4. `px4_external_pose_bridge`

Reason:

- the current slice is only meant to prove DDS connectivity, message compatibility, and frame conversion
- offboard control should not be added before connectivity and state packaging are stable

## Acceptance Criteria For This First Slice

The current first slice is acceptable when all of these are true:

1. `px4_msgs` builds inside the VNV workspace
2. `venom_px4_bridge` builds cleanly against that pinned message set
3. `ros2 launch venom_bringup px4_agent_probe.launch.py` starts without missing-package errors
4. `/fmu/out/*` topics appear when PX4 DDS is live
5. `/px4_bridge/agent_status` reports healthy when timesync is present
6. `/px4_bridge/odom` is published in ROS ENU/FLU coordinates

## Honest Status On This Machine

Repository preparation is complete for the first PX4 slice.

What is not verified locally in this session:

- ROS 2 Humble is not present at `/opt/ros/humble`
- `MicroXRCEAgent` is not installed in the current environment
- therefore `colcon build` and runtime launch were not executed locally here

So the repository side is prepared, but environment-side verification still has to happen on a ROS/PX4-ready host.
