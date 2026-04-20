---
title: Architecture
permalink: /en/architecture
desc: Understand the layered structure of drivers, perception, localization, planning, system orchestration, and simulation.
breadcrumb: Modules & Interfaces
layout: default
---

## System View

Venom VNV can be understood as six layers:

1. Drivers
2. Perception
3. Localization
4. Planning
5. System orchestration
6. Simulation

## Layer Responsibilities

| Layer | Responsibility |
| --- | --- |
| Drivers | `driver/` packages for sensors, chassis, arms, serial links, and PX4 bridges |
| Perception | `perception/` packages for detection, recognition, tracking, and auto aim |
| Localization | `localization/` packages for LIO, odometry, and relocalization |
| Planning | reserved `planning/` space for planners such as `ego_planner` |
| System | bringup, robot description, task orchestration, and mode composition |
| Simulation | standalone simulation workspaces and regression baselines |

## Directory Mapping

| Layer | Main Directories | Description |
| --- | --- | --- |
| Drivers | `driver/` | Hardware-facing drivers and bridges |
| Perception | `perception/` | Detection, auto aim, and general vision modules |
| Localization | `localization/` | LIO, 2D odometry, and relocalization |
| Planning | `planning/` (reserved) | Planned home for trajectory and motion planners |
| System | `venom_bringup`, `venom_robot_description` | Robot-level composition and description |
| Simulation | `simulation/venom_nav_simulation` | Simulation workspace for navigation and LIO validation |

## Design Principle

- drivers expose hardware capabilities
- perception produces structured observations
- localization owns pose and map-alignment estimates
- planning owns paths and trajectories, not mission logic
- system composition ties modules together into robot modes
- simulation stays isolated from deployment-oriented packages

## Why This Structure Matters

The project tries to keep the layers reusable across robot forms. That is why the documentation emphasizes:

- Stable ROS 2 topics
- Stable TF names
- Clear package boundaries
- Bringup-level composition instead of hard coupling
