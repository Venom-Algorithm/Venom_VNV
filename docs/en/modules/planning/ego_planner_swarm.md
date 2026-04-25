---
title: Ego Planner Swarm
description: ego-planner-swarm - ROS 2 UAV local planning and swarm-planning submodule.
---

## Module Role

`planning/navigation/ego-planner-swarm` is the ROS 2 planning submodule imported from ZJU FAST Lab. The tracked branch is `ros2_version`.

It belongs to the planning layer. It owns UAV local trajectory generation, obstacle avoidance, and swarm-planning validation. It does not own waypoint orchestration, behavior trees, or state monitoring.

## Directory

```text
planning/navigation/ego-planner-swarm
```

Current `.gitmodules` entry:

```text
url = https://github.com/ZJU-FAST-Lab/ego-planner-swarm.git
branch = ros2_version
```

## Main Packages

| Directory | Role |
| --- | --- |
| `src/planner/plan_manage` | planner orchestration and launch entry points |
| `src/planner/plan_env` | local map and environment representation |
| `src/planner/path_searching` | path searching |
| `src/planner/bspline_opt` | B-spline trajectory optimization |
| `src/planner/traj_utils` | trajectory messages and helpers |
| `src/uav_simulator/*` | upstream UAV simulation and map-generation tools |

## DDS Requirement

The upstream README recommends CycloneDDS because the default FastDDS path can show significant runtime lag.

Install:

```bash
sudo apt install ros-humble-rmw-cyclonedds-cpp
```

Switch the current terminal:

```bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
```

Persist it in the shell:

```bash
echo "export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp" >> ~/.bashrc
source ~/.bashrc
```

Verify:

```bash
ros2 doctor --report | grep "RMW middleware"
```

## Common Commands

Launch RViz:

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch ego_planner rviz.launch.py
```

Single-drone simulation:

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch ego_planner single_run_in_sim.launch.py
```

Swarm simulation:

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch ego_planner swarm.launch.py
```

Large-swarm simulation:

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch ego_planner swarm_large.launch.py
```

Run with optional arguments:

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch ego_planner single_run_in_sim.launch.py use_mockamap:=True use_dynamic:=False
```

Arguments:

| Argument | Meaning | Default |
| --- | --- | --- |
| `use_mockamap` | Map generation mode. `False` uses Random Forest; `True` uses mockamap. | `False` |
| `use_dynamic` | Whether to consider dynamics. | `False` |

## Boundary In VNV

- `ego-planner-swarm` stays under `planning/navigation/`
- waypoint dispatch, task switching, and global monitoring belong under `mission/`
- PX4 external-pose bridging should be assembled through `driver/venom_px4_bridge` and `venom_bringup`

## Related Pages

- [Planning](index.md)
- [PX4 Bridge](../drivers/venom_px4_bridge.md)
- [Launch & Use](../../home/launch_usage.md)
