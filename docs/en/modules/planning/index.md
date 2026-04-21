---
title: Planning
permalink: /en/planning_overview
desc: Overview of navigation planners, controllers, and manipulation motion planning modules.
breadcrumb: Modules & Interfaces
layout: default
---

## Layer Role

The planning layer is responsible for:

- generating paths or trajectories from goals, maps, and robot state
- local obstacle avoidance
- motion feasibility and trajectory shaping
- generating motion plans for manipulation tasks such as grasp execution

It is not responsible for:

- raw hardware access
- pure localization estimation
- waypoint logic, behavior trees, or task dispatch

## Recommended Directory Name

```text
planning/
```

Modules such as `ego_planner`, TEB, custom Nav2 controllers, and MoveIt grasp planning should live here.

## Current Status

The main workspace now contains a committed `planning/` directory with placeholder `navigation/` and `manipulation/` subfolders.

## Current Layout Pattern

```text
planning/
├── navigation/
│   ├── venom_eagle_planner/
│   ├── venom_teb_controller/
│   └── venom_nav_controller_xxx/
└── manipulation/
    └── venom_moveit_grasp/
```

## Boundary With The Mission Layer

- `planning/` answers “how to move”
- `mission/` answers “when to dispatch goals, switch tasks, and advance flows”

Those concerns should stay separated.

## Related Pages

- [Architecture]({{ '/en/architecture' | relative_url }})
- [Mission]({{ '/en/mission_overview' | relative_url }})
- [System]({{ '/en/integration_overview' | relative_url }})
- [Simulation]({{ '/en/simulation_overview' | relative_url }})
