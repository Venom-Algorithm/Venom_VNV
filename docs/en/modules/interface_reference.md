---
title: Modules & Interfaces
permalink: /en/interface_reference
desc: High-level structure of the system modules, interface constraints, and entry points to sub-documents.
breadcrumb: Modules & Interfaces
layout: default
---

## Reading Guide

This section is meant to answer two questions:

1. What major module groups exist in the repository?
2. What interface constraints should stay stable across implementations?

## Main Categories

- [Architecture]({{ '/en/architecture' | relative_url }})
- [Drivers]({{ '/en/driver_overview' | relative_url }})
- [Perception]({{ '/en/perception_overview' | relative_url }})
- [Localization]({{ '/en/localization_overview' | relative_url }})
- [Planning]({{ '/en/planning_overview' | relative_url }})
- [Mission]({{ '/en/mission_overview' | relative_url }})
- [System]({{ '/en/integration_overview' | relative_url }})
- [Simulation]({{ '/en/simulation_overview' | relative_url }})
- [Topic Reference]({{ '/en/topics' | relative_url }})
- [TF Tree]({{ '/en/tf_tree' | relative_url }})

## Recommended Layering

1. `driver/`: hardware-facing integration and bridges
2. `perception/`: detection, recognition, and tracking
3. `localization/`: LIO, odometry, and relocalization
4. `planning/`: navigation planners, controllers, and manipulation motion planning
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
