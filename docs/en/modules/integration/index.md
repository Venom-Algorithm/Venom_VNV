---
title: System Layer
description: Overview of startup orchestration, robot description, and robot-level
  entry points.
---

## Covered Modules

- [System Bringup](venom_bringup.md)
- [Robot Description](venom_robot_description.md)

## Layer Role

Single packages answer “how one module runs.”  
The system layer answers “how the whole robot runs together.”

`multi_waypoint_commander` and `mission_controller/` are currently still maintained inside `venom_bringup`. This is a transitional state kept to avoid breaking existing launch and parameter paths.

## Why This Is Not Planning

- the system layer composes modules and modes
- it does not own trajectory-generation algorithms
- planners such as `ego-planner-swarm` and `venom_teb_controller` should live under `planning/`

## Why This Is Not Mission

- the mission layer owns waypoint, BT, monitor, and task-progression packages
- the system layer assembles those packages into robot-level bringup modes
- future task packages should not keep growing inside `venom_bringup`

New standalone mission packages should still be placed under `mission/`.
