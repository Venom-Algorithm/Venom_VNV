---
title: Mission Layer
permalink: /en/mission_overview
desc: Unified entry for behavior trees, state monitoring, goal dispatch, and mission-execution modules.
breadcrumb: Modules & Interfaces
layout: default
---

## Layer Role

The mission layer answers two questions:

1. what the robot should do now
2. who dispatches, monitors, and advances that task

It does not own low-level trajectory generation, and it is not a hardware-facing layer.

## Recommended Directory Layout

```text
mission/
├── navigation/
└── manipulation/
```

Recommended organization:

```text
mission/
├── navigation/
│   ├── venom_waypoint/
│   ├── venom_nav_bt/
│   ├── venom_global_monitor/
│   └── venom_mission_manager/
└── manipulation/
    ├── venom_grasp_mission/
    └── venom_pick_place_manager/
```

## Boundary Against Planning

- `planning/` answers how to generate paths, trajectories, and control outputs
- `mission/` answers when to dispatch goals, switch tasks, and react to state transitions

Examples:

- `venom_eagle_planner` and `venom_teb_controller` belong under `planning/navigation/`
- `venom_waypoint`, `venom_nav_bt`, and `venom_global_monitor` belong under `mission/navigation/`
- `venom_moveit_grasp` belongs under `planning/manipulation/`
- `venom_grasp_mission` belongs under `mission/manipulation/`

## Recommended Package Names

- navigation task entry: `venom_waypoint`
- navigation behavior tree: `venom_nav_bt`
- global state monitor: `venom_global_monitor`
- mission manager: `venom_mission_manager`
- grasp-task flow: `venom_grasp_mission`

## Current Status

The main workspace now contains a committed `mission/` directory with placeholder `navigation/` and `manipulation/` subfolders.

Future behavior-tree, waypoint, listener, and task-dispatch packages should be placed here instead of continuing to grow inside `venom_bringup`.

## Related Pages

- [Architecture]({{ '/en/architecture' | relative_url }})
- [Planning]({{ '/en/planning_overview' | relative_url }})
- [System]({{ '/en/integration_overview' | relative_url }})
