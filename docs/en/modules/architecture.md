---
title: Architecture
description: Understand the frozen layered structure of drivers, perception, localization,
  planning, mission, system, and simulation.
---

## System View

Venom VNV can be understood as seven layers:

1. Drivers
2. Perception
3. Localization
4. Planning
5. Mission
6. System orchestration
7. Simulation

## Layer Responsibilities

| Layer | Responsibility |
| --- | --- |
| Drivers | `driver/` packages for sensors, chassis, arms, serial links, and PX4 bridges |
| Perception | `perception/` packages for detection, recognition, tracking, and auto aim |
| Localization | `localization/` packages for LIO, odometry, and relocalization |
| Planning | `planning/` for planners, controllers, and manipulation motion planning |
| Mission | `mission/` for waypoint, behavior-tree, monitor, and task-management packages |
| System | bringup, robot description, and mode composition |
| Simulation | standalone simulation workspaces and regression baselines |

## Directory Mapping

| Layer | Main Directories | Description |
| --- | --- | --- |
| Drivers | `driver/` | Hardware-facing drivers and bridges |
| Perception | `perception/` | Detection, auto aim, and general vision modules |
| Localization | `localization/` | LIO, 2D odometry, and relocalization |
| Planning | `planning/` | Home for navigation planners, controllers, and MoveIt-side motion planning |
| Mission | `mission/` | Home for waypoint, BT, monitor, and mission-management packages |
| System | `venom_bringup`, `venom_robot_description` | Robot-level composition and description, not mission-package ownership |
| Simulation | `simulation/venom_nav_simulation` | Simulation workspace for navigation and LIO validation |

## Design Principle

- drivers expose hardware capabilities
- perception produces structured observations
- localization owns pose and map-alignment estimates
- planning owns paths, trajectories, and control-side motion generation
- mission owns behavior trees, dispatch, monitors, and task progression
- system composition ties modules together into robot modes
- simulation stays isolated from deployment-oriented packages

## Why This Structure Matters

The project tries to keep the layers reusable across robot forms. That is why the documentation emphasizes:

- Stable ROS 2 topics
- Stable TF names
- Clear package boundaries
- Bringup-level composition instead of hard coupling
