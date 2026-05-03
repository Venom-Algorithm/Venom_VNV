---
title: Mission Layer
description: Unified entry for behavior trees, state monitoring, goal dispatch, and
  mission-execution modules.
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

- `ego-planner-swarm` and `venom_teb_controller` belong under `planning/navigation/`
- `venom_waypoint`, `venom_nav_bt`, and `venom_global_monitor` belong under `mission/navigation/`
- arm-side motion-planning packages belong under `planning/manipulation/`
- grasp-task flow packages belong under `mission/manipulation/`

## Recommended Package Names

- navigation task entry: `venom_waypoint`
- navigation behavior tree: `venom_nav_bt`
- global state monitor: `venom_global_monitor`
- mission manager: `venom_mission_manager`
- grasp-task flow: use a task-specific name later, for example `venom_grasp_mission`

## Current Status

The main workspace now contains a committed `mission/` directory with reserved `navigation/` and `manipulation/` subfolders.

Those folders are the target home for future standalone mission packages. The runnable mission-control implementation that exists today is still inside `venom_bringup`:

| Current implementation | Path | Role |
| --- | --- | --- |
| Multi-waypoint entry | `venom_bringup/venom_bringup/multi_waypoint_commander.py` | reads `waypoints.yaml` and calls Nav2 Simple Commander `followWaypoints()` |
| Health-aware entry | `venom_bringup/venom_bringup/health_aware_commander.py` | adds state monitoring, return-to-base, and recovery logic around waypoint navigation |
| Mission-control core | `venom_bringup/venom_bringup/mission_controller/` | provides state monitoring, mission-state management, and behavior-plugin abstractions |
| Mission plugins | `venom_bringup/venom_bringup/plugins/` | currently includes health-state and navigation-task plugins |
| Config files | `venom_bringup/config/scout_mini/mission_config.yaml`, `venom_bringup/config/scout_mini/waypoints.yaml` | current Scout Mini mission-control examples |

The current rule is:

1. use existing mission-control features through `venom_bringup` launch files or `multi_waypoint_commander`
2. place new standalone mission packages under `mission/navigation/` or `mission/manipulation/`
3. if the existing code is migrated later, launch files, parameter paths, and documentation links must move together

## Current Runnable Entries

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch venom_bringup health_aware_navigation.launch.py
```

Or run the console script directly:

```bash
cd ~/venom_ws
source install/setup.bash
ros2 run venom_bringup multi_waypoint_commander
```

## Related Pages

- [Architecture](../architecture.md)
- [Planning](../planning/index.md)
- [System](../integration/index.md)
