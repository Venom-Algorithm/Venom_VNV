---
title: Architecture
permalink: /en/architecture
desc: Understand the four-layer structure of perception, localization, decision, and actuation.
breadcrumb: Modules & Interfaces
layout: default
---

## System View

Venom VNV can be understood as four large layers:

1. Perception
2. Localization
3. Decision / task orchestration
4. Actuation / robot interface

## Layer Responsibilities

| Layer | Responsibility |
| --- | --- |
| Perception | Camera, LiDAR, detector, tracker, solver, and related pipelines |
| Localization | LIO, odometry, relocalization, and map-alignment logic |
| Decision | Bringup composition, task logic, and robot-level mode switching |
| Actuation | Chassis, arm, serial controller, and low-level execution |

## Why This Structure Matters

The project tries to keep the layers reusable across robot forms. That is why the documentation emphasizes:

- Stable ROS 2 topics
- Stable TF names
- Clear package boundaries
- Bringup-level composition instead of hard coupling
