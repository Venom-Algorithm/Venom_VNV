---
title: Updates & Migration
description: Repository migration, submodule strategy, and compatibility notes.
---

## What This Page Covers

This page is used to record:

- repository remote changes
- submodule URL updates
- structural doc changes
- compatibility notes between older and newer workspace layouts

## Current Direction

The repository has been moving from personal ownership toward organization-managed repositories. As part of that process:

- the main repository and submodules need consistent remote rules
- `.gitmodules` should stay friendly for cloning
- deployment documentation should stay aligned with the actual repository structure

## Current Rules

- `.gitmodules` uses HTTPS so non-maintainers can clone recursively
- maintainers may keep SSH `pushurl` locally for push access
- profile-based submodule checkout should use the root Makefile, for example `make submodules-uav`
- CI / Docker builds may write `COLCON_IGNORE` temporarily to skip hardware-only or platform-specific packages; that file should not be committed

## Recent Structure Changes

| Change | Meaning |
| --- | --- |
| `planning/navigation/ego-planner-swarm` | new Ego Planner Swarm ROS 2 submodule tracking `ros2_version` |
| `venom_bringup/launch/examples/px4_vps_bridge.launch.py` | new PX4 external-pose bridge entry point |
| `docker/Dockerfile.sim`, `docker-compose.yml` | new Docker sim environment |
| root `Makefile` profiles | new `submodules-ugv`, `submodules-sim`, `submodules-uav`, and related selective checkout targets |
