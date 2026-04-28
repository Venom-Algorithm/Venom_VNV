---
title: TEB Controller
description: venom_teb_controller - TEB local planner integrated as a Nav2 controller plugin.
---

## Module Role

`planning/navigation/venom_teb_controller` is the current 2D local trajectory optimization and controller submodule.

It provides a Nav2 controller plugin instead of a standalone robot bringup entry:

| Item | Current Value |
| --- | --- |
| Submodule path | `planning/navigation/venom_teb_controller` |
| Controller package | `teb_local_planner` |
| Message package | `teb_msgs` |
| Plugin type | `teb_local_planner::TebLocalPlannerROS` |
| Plugin declaration | `planning/navigation/venom_teb_controller/venom_teb_controller/teb_local_planner_plugin.xml` |
| Default params | `venom_teb_controller/params/teb_params.yaml` |

In the VNV structure, this belongs to `planning/navigation/`. It handles local path tracking, obstacle avoidance, and trajectory optimization. It does not own waypoint dispatch, behavior trees, or mission logic.

## Nav2 Integration

The package exports a Nav2 controller plugin through `package.xml`:

```xml
<nav2_core plugin="${prefix}/teb_local_planner_plugin.xml" />
```

The plugin type declared in XML is:

```xml
teb_local_planner::TebLocalPlannerROS
```

Use it by loading the plugin from Nav2 `controller_server` parameters, not as a standalone launch entry.

## Interfaces

| Direction | Interface | Notes |
| --- | --- | --- |
| Input | Nav2 global path | passed into controller server by the Nav2 planning / BT flow |
| Input | `/odom` | default `odom_topic` in the current params |
| Input | costmap | provided by Nav2 controller server |
| Output | `cmd_vel` | published by Nav2 controller server |
| Output | TEB feedback / visualization | controlled by parameters such as `publish_feedback` |

## Current Launch Status

This submodule currently provides no standalone `.launch.py` file. The correct integration path is:

1. add the TEB plugin parameters to the Nav2 `controller_server`
2. make sure `teb_local_planner` and `teb_msgs` are built
3. start Nav2 from the upper-level bringup and let Nav2 load the controller plugin

## Key Parameters

| Parameter | Purpose | Default |
| --- | --- | --- |
| `controller_frequency` | Nav2 controller update rate in Hz. | `5.0` |
| `odom_topic` | Odometry topic used by the controller. | `/odom` |
| `controller_plugins` | Loaded controller plugin instance names. | `["FollowPath"]` |
| `controller_plugin_types` | Controller plugin type list. | `["teb_local_planner::TebLocalPlannerROS"]` |
| `dt_ref` | Target temporal distance between trajectory samples. | `0.3` |
| `max_global_plan_lookahead_dist` | Maximum global-plan lookahead distance in meters. | `3.0` |
| `max_vel_x` | Maximum forward velocity in m/s. | `0.26` |
| `max_vel_theta` | Maximum yaw velocity in rad/s. | `1.0` |
| `acc_lim_x` | Linear acceleration limit in m/s². | `2.5` |
| `acc_lim_theta` | Angular acceleration limit in rad/s². | `3.2` |
| `footprint_model.type` | Robot footprint model type. | `"circular"` |
| `footprint_model.radius` | Circular footprint radius in meters. | `0.17` |
| `min_obstacle_dist` | Desired minimum obstacle distance in meters. | `0.27` |
| `inflation_dist` | Obstacle inflation influence distance in meters. | `0.6` |
| `include_costmap_obstacles` | Whether costmap obstacles are included. | `True` |
| `enable_homotopy_class_planning` | Whether to evaluate multiple homotopy classes. | `True` |
| `max_number_classes` | Maximum number of homotopy candidates. | `4` |
| `optimization_activate` | Whether trajectory optimization is active. | `True` |
| `weight_obstacle` | Obstacle-distance cost weight. | `100.0` |
| `weight_viapoint` | Weight for following global-plan via-points. | `50.0` |

## Boundary

- `venom_teb_controller` is loaded as a Nav2 controller plugin
- mission goals belong under `mission/navigation/`
- maps, costmaps, and footprints are owned by Nav2 parameters and robot description
- if `costmap_converter_plugin` is enabled, the runtime environment must provide that plugin; otherwise disable or replace it in the active Nav2 params

## Related Pages

- [Planning](index.md)
- [Architecture](../architecture.md)
- [Simulation](../simulation/index.md)
- [Mission](../mission/index.md)
