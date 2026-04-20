---
title: 定位层
permalink: /localization_overview
desc: LIO、2D 里程计、重定位与地图对齐相关模块总览。
breadcrumb: 模块与接口
layout: default
---

## 层级职责

定位层负责两类事情：

1. 生成连续局部位姿，例如 `odom -> base_link`
2. 在需要时恢复全局参考，例如 `map -> odom`

## 当前模块

- [LIO 总览]({{ '/lio_overview' | relative_url }})
- [Point-LIO]({{ '/point_lio' | relative_url }})
- [Fast-LIO]({{ '/fast_lio' | relative_url }})
- [rf2o 激光里程计]({{ '/rf2o_laser_odometry' | relative_url }})
- [重定位]({{ '/small_gicp_relocalization' | relative_url }})

## 模块关系

- `LIO` 子层负责 3D 主里程计输出
- `rf2o_laser_odometry` 负责轻量 2D 运动估计
- `small_gicp_relocalization` 负责恢复全局 `map -> odom`

## 当前目录映射

- `localization/lio/`
- `localization/relocalization/`

## 推荐阅读顺序

1. [LIO 总览]({{ '/lio_overview' | relative_url }})
2. [Point-LIO]({{ '/point_lio' | relative_url }})
3. [重定位]({{ '/small_gicp_relocalization' | relative_url }})
4. [rf2o 激光里程计]({{ '/rf2o_laser_odometry' | relative_url }})
