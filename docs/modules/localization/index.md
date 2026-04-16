---
title: 定位建图
permalink: /localization_overview
desc: 3D 里程计、2D 补充里程计与全局重定位模块总览。
breadcrumb: 模块与接口
layout: default
---

## 核心模块

- [Point-LIO]({{ '/point_lio' | relative_url }})
- `Fast-LIO`（后续补充文档）
- [rf2o 激光里程计]({{ '/rf2o_laser_odometry' | relative_url }})
- [重定位]({{ '/small_gicp_relocalization' | relative_url }})

## 模块关系

- `Point-LIO` 负责主里程计输出
- `rf2o_laser_odometry` 负责轻量平面辅助定位
- `small_gicp_relocalization` 负责恢复全局 `map -> odom`

## 推荐阅读顺序

1. `Point-LIO`
2. `small_gicp_relocalization`
3. `rf2o_laser_odometry`
