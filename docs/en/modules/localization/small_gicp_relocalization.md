---
title: Relocalization
description: small_gicp_relocalization — Global relocalization through point-cloud
  registration.
---

## Module Role

`small_gicp_relocalization` is responsible for global relocalization against an existing map.

## System Contract

In the overall system, this module should mainly be thought of as the place that recovers or refines the `map -> odom` relationship.

## Current Entries

| File | Purpose |
| --- | --- |
| `small_gicp_relocalization_launch.py` | original example launch with parameters hardcoded in the file |
| `relocalization.launch.py` | VNV-facing launch used by upper-level bringup, with launch arguments such as `prior_pcd_file` |
| `prior_map_publisher.launch.py` | publishes a prior PCD as `/prior_map` for visualization/debugging |

Full-system bringup should normally go through `venom_bringup`:

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch venom_bringup relocalization_bringup.launch.py \
  pcd_file:=$HOME/venom_ws/src/venom_vnv/localization/lio/Point-LIO/PCD/scans.pcd
```

For a focused node-only run:

```bash
cd ~/venom_ws
source install/setup.bash
ros2 run small_gicp_relocalization small_gicp_relocalization_node --ros-args \
  -p prior_pcd_file:=$HOME/venom_ws/src/venom_vnv/localization/lio/Point-LIO/PCD/scans.pcd \
  -p input_cloud_topic:=cloud_registered \
  -p base_frame:=base_link \
  -p robot_base_frame:=base_link \
  -p lidar_frame:=laser_link
```

## Key Parameters

| Parameter | Purpose | Default |
| --- | --- | --- |
| `num_threads` | Registration thread count. | `4` |
| `num_neighbors` | Neighbor count for covariance estimation. | `20` in source, `10` in the VNV-facing launch |
| `global_leaf_size` | Voxel size for the prior map, in meters. | `0.25` |
| `registered_leaf_size` | Voxel size for the incoming registered cloud, in meters. | `0.25` |
| `max_dist_sq` | Squared correspondence rejection threshold. | `1.0` |
| `map_frame` | Global map frame. | `"map"` |
| `odom_frame` | Local odometry frame. | `"odom"` |
| `base_frame` | Robot base frame used when transforming the prior map. | `""` |
| `robot_base_frame` | Robot base frame used when applying `initialpose`. | `""` |
| `lidar_frame` | LiDAR frame used for TF lookup. | `""` |
| `prior_pcd_file` | Prior PCD map path. | `""` |
| `input_cloud_topic` | Input registered cloud topic. | `"registered_scan"` in source, usually `cloud_registered` in VNV launches |
