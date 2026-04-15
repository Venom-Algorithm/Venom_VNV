---
title: LIO
desc: LiDAR-Inertial Odometry 模块的整体约束、统一接口与子算法入口。
breadcrumb: 模块与接口
layout: default
---

## LIO 在系统里的职责

LIO 模块负责提供机器人本体的连续局部位姿估计，是系统中的主定位源之一。

在当前 VNV 体系里，LIO 需要承担：

- 发布 `/odom`
- 发布 `odom -> base_link` 变换
- 输出配准后的点云
- 在需要时输出三维地图点云

## 统一约束

后续接入任何新的 LIO，都必须遵守这组接口约束。

### TF 约束

- LIO 负责 `odom -> base_link`
- 不负责 `map -> odom`
- 传感器安装位姿保持静态，不在运行时改整棵 TF 树
- 主 TF 只能有一套有效来源，不能同时存在多套 `odom -> base_link`

### Topic 约束

- 里程计输出统一为 `/odom`
- 配准后点云输出统一包含 `/cloud_registered` 和 `/cloud_registered_body`
- 地图点云输出统一为 `/map_cloud`
- 路径输出统一为 `/path`

### Frame 约束

- `/odom` 的 `header.frame_id` 必须为 `odom`
- `/odom` 的 `child_frame_id` 必须为 `base_link`
- `/cloud_registered` 的 `frame_id` 必须为 `odom`
- `/cloud_registered_body` 的 `frame_id` 必须为 `base_link`
- `/map_cloud` 的 `frame_id` 必须为 `odom`

### 地图语义约束

- 每个 LIO 都可以保留自己的内部地图结构，例如 `iVox` 或 `ikd-tree`
- 内部地图只服务在线配准，不直接作为上层接口语义暴露
- `/map_cloud` 必须视为低频、稀疏、面向可视化的地图输出
- 导出的 PCD 必须来自内部配准地图，而不是直接从 `/map_cloud` 导出

### 参数结构约束

后续接入的新 LIO，配置文件应尽量遵守这组分层：

- 顶层公共基础参数
- `common`
- `preprocess`
- `mapping`
- `odometry`
- `publish`
- `frame`
- `pcd_save`

### 推荐默认命名

- `publish.odom_topic = "odom"`
- `publish.cloud_registered_topic = "cloud_registered"`
- `publish.cloud_registered_body_topic = "cloud_registered_body"`
- `publish.map_topic = "map_cloud"`
- `publish.path_topic = "path"`
- `frame.odom_frame_id = "odom"`
- `frame.base_frame_id = "base_link"`
- `frame.cloud_registered_frame_id = "odom"`
- `frame.cloud_registered_body_frame_id = "base_link"`
- `frame.map_frame_id = "odom"`

## 子算法文档

- [Point-LIO](point_lio.md)
- [Fast-LIO](fast_lio.md)

## 说明

不同 LIO 算法可以有不同内部实现，但进入系统后，必须表现成相同的接口角色，不能把各自原生的命名习惯直接暴露给上层模块。
