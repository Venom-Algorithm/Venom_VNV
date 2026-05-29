---
title: 定位层
description: LIO、2D 里程计与后续全局定位接口相关模块总览。
---

## 层级职责

定位层负责两类事情：

1. 生成连续局部位姿，例如 `odom -> base_link`
2. 为后续全局定位 / 重定位模块保留 `map -> odom` 接口约定

## 当前模块

- [LIO 总览](../lio/index.md)
- [Point-LIO](../lio/point_lio.md)
- [Fast-LIO](../lio/fast_lio.md)
- [rf2o 激光里程计](rf2o_laser_odometry.md)

## 模块关系

- `LIO` 子层负责 3D 主里程计输出
- `rf2o_laser_odometry` 负责轻量 2D 运动估计
- GICP 重定位子模块当前因稳定性问题暂时下线，不再作为主仓库 submodule 拉取

## 当前目录映射

- `localization/lio/`
- `localization/relocalization/` 作为全局定位 / 重定位模块预留目录

## 推荐阅读顺序

1. [LIO 总览](../lio/index.md)
2. [Point-LIO](../lio/point_lio.md)
3. [rf2o 激光里程计](rf2o_laser_odometry.md)
