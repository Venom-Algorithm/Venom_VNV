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
| Perception | `perception/` packages for auto aim, YOLO detection, QR/barcode recognition, and tracking |
| Localization | `localization/` packages for LIO, odometry, and future global-localization interfaces |
| Planning | `planning/` for Ego Planner, TEB controller, Nav2 controllers, and manipulation motion planning |
| Mission | `mission/` for new waypoint, behavior-tree, monitor, and task-management packages; the current mission-control framework still lives under `venom_bringup/venom_bringup/mission_controller` |
| System | bringup, robot description, mode composition, and the current transitional mission-control entry |
| Simulation | standalone simulation workspaces and regression baselines |

## Directory Mapping

| Layer | Main Directories | Description |
| --- | --- | --- |
| Drivers | `driver/` | Hardware-facing drivers and bridges |
| Perception | `perception/` | Auto aim, YOLO detection, QR/barcode recognition, and general vision modules |
| Localization | `localization/` | LIO, 2D odometry, and future global-localization interfaces |
| Planning | `planning/` | Home for Ego Planner, TEB controller, Nav2 controllers, and MoveIt-side motion planning |
| Mission | `mission/`, current mission code under `venom_bringup/venom_bringup/mission_controller` | Home for waypoint, BT, monitor, and mission-management packages |
| System | `venom_bringup`, `venom_robot_description` | Robot-level composition and description; `venom_bringup` currently hosts part of the historical mission-control implementation |
| Simulation | `simulation/venom_nav_simulation` | Simulation workspace for navigation and LIO validation |

## Design Principle

- drivers expose hardware capabilities
- perception produces structured observations
- localization owns pose, odometry, and future global-localization interface contracts
- planning owns paths, trajectories, and control-side motion generation
- mission owns behavior trees, dispatch, monitors, and task progression
- system composition ties modules together into robot modes; existing mission-control code inside `venom_bringup` is treated as a transitional implementation
- simulation stays isolated from deployment-oriented packages

## Current Transitional State

Architecturally, new waypoint, behavior-tree, monitor, and mission-management packages belong under `mission/`. In the current repository, the runnable `multi_waypoint_commander`, `mission_controller/`, and `plugins/` implementations are still maintained inside `venom_bringup`.

This means:

1. daily use still enters these task features through `venom_bringup` launch files or console scripts
2. new standalone mission packages should be placed under `mission/`
3. if existing mission-control code is migrated later, launch files, parameter paths, and this page must be updated together

## Why This Structure Matters

The project tries to keep the layers reusable across robot forms. That is why the documentation emphasizes:

- Stable ROS 2 topics
- Stable TF names
- Clear package boundaries
- Bringup-level composition instead of hard coupling
