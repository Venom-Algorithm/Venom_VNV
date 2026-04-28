---
title: Planning
description: Overview of navigation planners, controllers, and manipulation motion
  planning modules.
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

Modules such as `ego-planner-swarm`, `venom_teb_controller`, custom Nav2 controllers, and MoveIt grasp planning live here.

## Current Status

The main workspace now contains a committed `planning/` directory. `planning/navigation/` already contains `ego-planner-swarm` and `venom_teb_controller`, while `planning/manipulation/` remains the entry point for arm-side motion planning.

## Current Layout Pattern

```text
planning/
├── navigation/
│   ├── ego-planner-swarm/
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

- [Architecture](../architecture.md)
- [Ego Planner Swarm](ego_planner_swarm.md)
- [TEB Controller](venom_teb_controller.md)
- [Mission](../mission/index.md)
- [System](../integration/index.md)
- [Simulation](../simulation/index.md)
