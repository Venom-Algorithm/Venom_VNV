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

### Topic 约束

- 里程计输出统一为 `/odom`
- 配准后点云输出统一包含 `/cloud_registered` 和 `/cloud_registered_body`
- 地图点云输出统一为 `/map_cloud`

### Frame 约束

- `/cloud_registered` 的 `frame_id` 必须为 `odom`
- `/cloud_registered_body` 的 `frame_id` 必须为 `base_link`
- `/map_cloud` 的 `frame_id` 必须为 `odom`

## 子算法文档

- [Point-LIO](point_lio.md)
- [Fast-LIO](fast_lio.md)

## 说明

不同 LIO 算法可以有不同内部实现，但进入系统后，必须表现成相同的接口角色，不能把各自原生的命名习惯直接暴露给上层模块。
