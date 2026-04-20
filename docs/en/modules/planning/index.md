---
title: Planning
permalink: /en/planning_overview
desc: Reserved layer for trajectory planning, obstacle avoidance, and motion-generation modules.
breadcrumb: Modules & Interfaces
layout: default
---

## Layer Role

The planning layer is responsible for:

- generating paths or trajectories from goals, maps, and robot state
- local obstacle avoidance
- motion feasibility and trajectory shaping

It is not responsible for:

- raw hardware access
- pure localization estimation
- robot-level mode orchestration

## Recommended Directory Name

```text
planning/
```

Modules such as `ego_planner` should live here rather than inside the system layer.

## Current Status

The main workspace does not yet carry a formal module under `planning/`. This layer is currently documented as a reserved architecture slot.

## Expected Future Layout

```text
planning/
├── ego_planner/
├── local_planner_xxx/
└── global_planner_xxx/
```

## Boundary With The System Layer

- `planning/` answers “how to move”
- the system layer answers “which mode to run and when”

Those concerns should stay separated.

## Related Pages

- [Architecture]({{ '/en/architecture' | relative_url }})
- [System]({{ '/en/integration_overview' | relative_url }})
- [Simulation]({{ '/en/simulation_overview' | relative_url }})
