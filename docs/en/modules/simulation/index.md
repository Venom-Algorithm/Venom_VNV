---
title: Simulation
permalink: /en/simulation_overview
desc: Overview of standalone simulation workspaces and simulation baselines separated from deployment packages.
breadcrumb: Modules & Interfaces
layout: default
---

## Layer Role

The simulation layer is responsible for:

- validating localization and navigation without real hardware
- carrying worlds, models, maps, and simulation-specific launch flows
- serving as a regression environment for algorithms and workflows

## Current Subproject

- [Navigation Simulation Workspace]({{ '/en/venom_nav_simulation' | relative_url }})

## Why This Is Separate

Simulation workspaces have very different dependencies and assets compared with deployment-oriented packages.

Keeping them separate helps:

1. avoid polluting the main deployment workspace
2. preserve stable regression environments
3. keep the Sim2Real boundary explicit

## Current Mapping

- `simulation/venom_nav_simulation`

## Related Pages

- [Architecture]({{ '/en/architecture' | relative_url }})
- [Localization]({{ '/en/localization_overview' | relative_url }})
- [Planning]({{ '/en/planning_overview' | relative_url }})
