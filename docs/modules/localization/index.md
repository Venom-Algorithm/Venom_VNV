---
title: 定位层
description: LIO、2D 里程计、重定位与地图对齐相关模块总览。
---

## 层级职责

定位层负责两类事情：

1. 生成连续局部位姿，例如 `odom -> base_link`
2. 在需要时恢复全局参考，例如 `map -> odom`

## 当前模块

- [LIO 总览](../lio/index.md)
- [Point-LIO](../lio/point_lio.md)
- [Fast-LIO](../lio/fast_lio.md)
- [rf2o 激光里程计](rf2o_laser_odometry.md)
- [重定位](small_gicp_relocalization.md)

## 模块关系

- `LIO` 子层负责 3D 主里程计输出
- `rf2o_laser_odometry` 负责轻量 2D 运动估计
- `small_gicp_relocalization` 负责恢复全局 `map -> odom`

## 当前目录映射

- `localization/lio/`
- `localization/relocalization/`

## 推荐阅读顺序

1. [LIO 总览](../lio/index.md)
2. [Point-LIO](../lio/point_lio.md)
3. [重定位](small_gicp_relocalization.md)
4. [rf2o 激光里程计](rf2o_laser_odometry.md)
