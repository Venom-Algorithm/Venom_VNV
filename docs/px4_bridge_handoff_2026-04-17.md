# PX4 Bridge Handoff

Date: 2026-04-17
Workspace: `~/venom_ws/src/venom_vnv`

## Current Structure

The PX4 integration is now organized as a project root under:

- `driver/venom_px4_bridge/`

That project root contains two ROS packages:

- `driver/venom_px4_bridge/px4_msgs`
- `driver/venom_px4_bridge/venom_px4_bridge`

This replaced the earlier flat layout where `driver/px4_msgs` existed as a top-level submodule and `driver/venom_px4_bridge` was only a single ROS package root.

## Why The Structure Changed

The user requested that PX4 support be maintained as one deeper subproject instead of two separate top-level pieces.

The resulting structure keeps:

- vendored official `px4_msgs`
- VNV-owned bridge implementation
- version constraints and deployment docs

inside one project boundary.

## Canonical Project Docs

Use these files as the current source of truth:

- `driver/venom_px4_bridge/README.md`
- `driver/venom_px4_bridge/COMPATIBILITY.md`
- `driver/venom_px4_bridge/docs/deployment.md`

## Fixed Baseline

- Ubuntu `22.04`
- ROS 2 `Humble`
- PX4 firmware line `v1.16.x`
- vendored `px4_msgs` upstream branch `release/1.16`
- vendored `px4_msgs` upstream base commit `392e831c1f659429ca83902e66820d7094591410`
- `Micro XRCE-DDS Agent v2.4.3`

## Current First Slice

The first PX4 slice currently includes:

- `px4_agent_monitor`
- `px4_status_adapter`
- `px4_agent_probe.launch.py`

Bridge-level outputs:

- `/px4_bridge/agent_status`
- `/px4_bridge/state`
- `/px4_bridge/odom`
- `/px4_bridge/health`

## Still Deferred

Not implemented yet:

1. `px4_mode_manager`
2. `px4_command_adapter`
3. `px4_offboard_test.launch.py`
4. `px4_external_pose_bridge`
