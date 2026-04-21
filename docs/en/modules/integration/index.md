---
title: System Layer
permalink: /en/integration_overview
desc: Overview of startup orchestration, robot description, and robot-level entry points.
breadcrumb: Modules & Interfaces
layout: default
---

## Covered Modules

- [System Bringup]({{ '/en/venom_bringup' | relative_url }})
- [Robot Description]({{ '/en/venom_robot_description' | relative_url }})

## Layer Role

Single packages answer “how one module runs.”  
The system layer answers “how the whole robot runs together.”

## Why This Is Not Planning

- the system layer composes modules and modes
- it does not own trajectory-generation algorithms
- planners such as `ego_planner` should live under `planning/`

## Why This Is Not Mission

- the mission layer owns waypoint, BT, monitor, and task-progression packages
- the system layer assembles those packages into robot-level bringup modes
- future task packages should not keep growing inside `venom_bringup`
