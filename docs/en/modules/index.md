---
title: Modules & Interfaces
description: High-level structure of the system modules, interface constraints, and
  entry points to sub-documents.
---

## Reading Guide

This section is meant to answer two questions:

1. What major module groups exist in the repository?
2. What interface constraints should stay stable across implementations?

## Main Categories

- [Architecture](architecture.md)
- [Drivers](drivers/index.md)
- [Perception](perception/index.md)
- [Localization](localization/index.md)
- [Planning](planning/index.md)
- [Ego Planner Swarm](planning/ego_planner_swarm.md)
- [Mission](mission/index.md)
- [System](integration/index.md)
- [Simulation](simulation/index.md)
- [Topic Reference](standards/topics.md)
- [TF Tree](standards/tf_tree.md)

## Recommended Layering

1. `driver/`: hardware-facing integration and bridges
2. `perception/`: detection, recognition, and tracking
3. `localization/`: LIO, odometry, and relocalization
4. `planning/`: navigation planners, controllers, and manipulation motion planning, currently including `ego-planner-swarm`
5. `mission/`: waypoint, behavior-tree, monitor, and mission-dispatch packages
6. `system/`: bringup, robot description, and robot-level assembly
7. `simulation/`: standalone simulation workspaces and baselines

## Core Principle

Different algorithms may be replaced over time, but the surrounding contracts should remain predictable:

- input topics
- output topics
- TF responsibilities
- naming conventions
- startup entry points
