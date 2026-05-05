---
title: Point-LIO
description: Point-LIO integration notes, MID360-facing behavior, and repository-specific
  interface conventions.
---

## Module Role

`Point-LIO` is currently one of the main 3D LiDAR-inertial odometry implementations used in the repository.

## What This Repository Cares About Most

- fixed TF conventions
- stable odometry output
- consistent registered cloud topics
- repository-specific parameter behavior for MID360 workflows

## In This Repository

The local fork has already been adjusted around:

- mapping defaults
- map publication behavior
- runtime stability fixes
- deployment-oriented parameter exposure
- runtime mode selection through `lio.operation_mode`
- realtime queue limits and async map publication / saving

## Current Config Files

- submodule config: `localization/lio/Point-LIO/config/mid360.yaml`
- submodule mapping config: `localization/lio/Point-LIO/config/mid360_mapping.yaml`
- VNV default online mapping config: `venom_bringup/config/examples/point_lio_mapping.yaml`
- VNV odom-only config: `venom_bringup/config/examples/point_lio_online_odom.yaml`
- VNV online odom + async map config: `venom_bringup/config/examples/point_lio_online_async_map.yaml`
- VNV offline mapping config: `venom_bringup/config/examples/point_lio_offline_map.yaml`

## Runtime Modes

Point-LIO now selects the main runtime behavior through `lio.operation_mode`:

| Mode | Typical config | Role |
| --- | --- | --- |
| `online_odom` | `point_lio_online_odom.yaml` | realtime odometry mode with map publication and PCD saving disabled for lower load |
| `online_odom_async_map` | `point_lio_mapping.yaml`, `point_lio_online_async_map.yaml` | realtime odometry plus an async map worker for map publication / PCD-related work |
| `offline_map` | `point_lio_offline_map.yaml` | reads rosbag2 from `lio.offline.bag_path` and saves a map to `lio.offline.output_pcd_path` |

Common launches:

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch venom_bringup mid360_point_lio.launch.py
```

Explicit async-map entry:

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch venom_bringup mid360_point_lio_async_map.launch.py
```

Odom-only launch:

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch venom_bringup mid360_point_lio_odom.launch.py
```

Offline mapping requires a rosbag2 directory:

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch venom_bringup mid360_point_lio_offline_map.launch.py \
  bag_path:=/absolute/path/to/rosbag2_dir \
  output_pcd_path:=/absolute/path/to/offline_map.pcd
```

Override the Point-LIO config when needed:

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch venom_bringup mid360_point_lio.launch.py \
  point_lio_cfg:=/absolute/path/to/point_lio_online_async_map.yaml
```

## Runtime Prompts and Warnings

Recent Point-LIO updates added operator-facing prompts and warning logs. Treat these as active runtime signals, not as harmless noise.

During startup, keep the LiDAR-IMU device stationary while these prompts are printed:

- `Point-LIO IMU initialization started. Keep the LiDAR-IMU device stationary...`
- `Building Point-LIO initial local map. Keep the LiDAR-IMU device stationary...`

Normal motion should only start after `Point-LIO initial local map is ready. Odometry tracking has started...` appears.

| Log keyword | Meaning | Typical action |
| --- | --- | --- |
| `dropped old LiDAR frame(s)` | realtime LiDAR queue exceeded `lio.realtime.max_lidar_queue` | reduce point-cloud load, check CPU load, tune queue depth, or use `online_odom` |
| `dropped old IMU sample(s)` | realtime IMU queue exceeded `lio.realtime.max_imu_queue` | check IMU rate, timestamps, DDS stalls, and process load |
| `dropped old map job(s)` | async map worker cannot keep up with map publication / saving jobs | increase `lio.async_map.queue_depth`, lower map publish rate, or make published maps sparser |
| `odometry loop overrun` | one odometry loop took longer than the LiDAR frame interval | reduce current-frame density, raise `filter_size_surf`, disable heavy outputs, or use `online_odom` |
| `abnormal LiDAR frame duration` | LiDAR frame duration differs significantly from `mapping.lidar_time_inte` | check timestamps, bag replay, driver config, and timestamp units |
| `waiting for IMU to cover LiDAR frame end` | IMU data has not reached the end time of the current LiDAR frame | check IMU latency, DDS stalls, and bag completeness |
| `IMU queue starts after LiDAR frame begin` | the early part of a LiDAR frame lacks IMU coverage | check startup order, truncated bags, dropped IMU data, and timestamp continuity |

## Important Parameters

| Parameter | Role | Current VNV default |
| --- | --- | --- |
| `lio.operation_mode` | selects `online_odom`, `online_odom_async_map`, or `offline_map` | `online_odom_async_map` |
| `lio.realtime.max_lidar_queue` | maximum LiDAR queue depth in realtime modes | `8` |
| `lio.realtime.max_imu_queue` | maximum IMU queue depth in realtime modes | `400` |
| `lio.async_map.queue_depth` | async map worker queue depth | `8` |
| `lio.async_map.drop_policy` | queue-full policy, currently only `drop_oldest` is supported | `drop_oldest` |
| `lio.offline.bag_path` | rosbag2 path for offline mapping | empty by default |
| `lio.offline.output_pcd_path` | offline PCD output path | `PCD/offline_map.pcd` |
| `filter_size_surf` | voxel size for current-scan downsampling | `0.05` |
| `filter_size_map_internal` | voxel size used by the internal map for registration | `0.2` |
| `filter_size_map_publish` | voxel size used only by the published map cloud | `0.2` |
| `filter_size_map_save` | voxel size used when exporting PCD | `0.2` |

## Note

The Chinese page remains the detailed reference for parameter-by-parameter explanations.
