---
title: Fast-LIO
desc: Fast-LIO 接入说明与系统内接口约束。
breadcrumb: 模块与接口
layout: default
---

# Fast-LIO

当前仓库已经将 `Fast-LIO` 接入为 `lio/Fast-LIO` 子模块。

## 模块定位

`Fast-LIO` 是系统中的另一套激光惯性里程计实现。它保留自身的核心算法，包括：

- 内部地图结构使用 `ikd-tree`
- scan-to-map 量测构造与迭代滤波流程保持 `Fast-LIO` 原始思路

但在进入整个 VNV 系统时，工程接口层必须与其他 LIO 统一。

## 统一工程目标

`Fast-LIO` 在本仓库中的目标接口应与 `Point-LIO` 保持一致：

- 输出 `/odom`
- 发布 `odom -> base_link`
- 输出 `/cloud_registered`
- 输出 `/cloud_registered_body`
- 输出 `/map_cloud`
- 路径输出 `/path`

并满足：

- `/cloud_registered.frame_id = odom`
- `/cloud_registered_body.frame_id = base_link`
- `/map_cloud.frame_id = odom`

## 地图与导图语义

在 VNV 体系里，`Fast-LIO` 需要遵守与 `Point-LIO` 相同的地图分层：

- 内部 `ikd-tree` 只服务在线配准
- `/map_cloud` 作为低频、稀疏、可视化地图
- PCD 导图直接来自内部配准地图，而不是直接从 `/map_cloud` 导出

## 相关文档

- [LIO 总览](lio_overview.md)
- [Point-LIO](point_lio.md)
