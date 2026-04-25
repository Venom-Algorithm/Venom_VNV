---
title: Simulation
description: Overview of standalone simulation workspaces and simulation baselines
  separated from deployment packages.
---

## Layer Role

The simulation layer is responsible for:

- validating localization and navigation without real hardware
- carrying worlds, models, maps, and simulation-specific launch flows
- serving as a regression environment for algorithms and workflows

## Current Subproject

- [Navigation Simulation Workspace](venom_nav_simulation.md)

## Why This Is Separate

Simulation workspaces have very different dependencies and assets compared with deployment-oriented packages.

Keeping them separate helps:

1. avoid polluting the main deployment workspace
2. preserve stable regression environments
3. keep the Sim2Real boundary explicit

## Current Mapping

- `simulation/venom_nav_simulation`
- `docker/Dockerfile.sim`
- `docker-compose.yml`
- `scripts/ci-colcon-build.sh`

## Docker Simulation Environment

The root repository now includes a Docker sim environment for consistent simulation dependencies and local CI reproduction:

```bash
cd ~/venom_ws/src/venom_vnv
make build
make up
make shell
make rosdep
make colcon
```

To reproduce the GitHub Actions headless build locally:

```bash
cd ~/venom_ws/src/venom_vnv
make ci-build
```

To clean containers and build caches:

```bash
cd ~/venom_ws/src/venom_vnv
make clean
```

The CI build temporarily writes `COLCON_IGNORE` files for hardware drivers, LIO submodules, and Gazebo Classic packages, and validates the subset that can build reliably inside the container.

## Related Pages

- [Architecture](../architecture.md)
- [Localization](../localization/index.md)
- [Planning](../planning/index.md)
