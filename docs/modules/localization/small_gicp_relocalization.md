---
title: 重定位
description: small_gicp_relocalization — 基于点云配准的全局重定位。
---

## 模块定位

`small_gicp_relocalization` 是系统中的全局重定位模块，负责：

- 读取先验地图
- 将当前局部点云与先验地图进行配准
- 估计 `map -> odom` 变换
- 为系统提供全局定位补偿

它和 LIO 的分工是：

- LIO 负责连续局部里程计 `odom -> base_link`
- 重定位负责全局对齐 `map -> odom`

## 输入与输出

| 方向 | 内容 | 说明 |
| --- | --- | --- |
| 订阅 | 当前局部点云 / 当前里程计 | 作为待配准输入 |
| 读取 | 先验 PCD 地图 | 作为目标地图 |
| 输出 | `map -> odom` | 全局修正变换 |

## 核心职责

- 加载先验地图
- 对当前扫描或局部子图做全局匹配
- 在匹配成功时更新全局参考关系
- 与局部 LIO 解耦，不替代 LIO 的高频局部估计

## 当前参数入口

当前常用启动入口：

- [`small_gicp_relocalization_launch.py`](https://github.com/Venom-Algorithm/Venom_VNV/blob/master/localization/relocalization/small_gicp_relocalization/launch/small_gicp_relocalization_launch.py)

核心参数在源码里声明：

- [`small_gicp_relocalization.cpp`](https://github.com/Venom-Algorithm/Venom_VNV/blob/master/localization/relocalization/small_gicp_relocalization/src/small_gicp_relocalization.cpp)

## 参数说明

| 参数名 | 作用 | 默认值 |
| --- | --- | --- |
| `num_threads` | 配准使用的线程数。 | `4` |
| `num_neighbors` | 协方差估计时每个点搜索的邻居数。邻居越多，局部结构估计越平滑。 | `20` |
| `global_leaf_size` | 先验地图体素降采样尺寸，单位米。 | `0.25` |
| `registered_leaf_size` | 当前输入点云体素降采样尺寸，单位米。 | `0.25` |
| `max_dist_sq` | 匹配拒绝门限，使用平方距离。值越小，离群匹配会被更严格地拒绝。 | `1.0` |
| `map_frame` | 全局地图坐标系。 | `"map"` |
| `odom_frame` | 局部里程计坐标系。 | `"odom"` |
| `base_frame` | 机器人机体系。某些 TF 初始化步骤会用到。 | `""` |
| `robot_base_frame` | 兼容性保留字段。当前代码里保留但未作为主要流程使用。 | `""` |
| `lidar_frame` | LiDAR 坐标系。用于初始化时查 TF。 | `""` |
| `prior_pcd_file` | 先验 PCD 地图路径。 | `""` |
| `init_pose` | 初始位姿 `[x, y, z, roll, pitch, yaw]`。用于给重定位一个初始猜测。 | `[0,0,0,0,0,0]` |
| `input_cloud_topic` | 待重定位点云输入话题。当前 launch 里通常接 `cloud_registered`。 | `"registered_scan"` |

## 参数联动理解

- `global_leaf_size` 决定先验地图密度
- `registered_leaf_size` 决定当前输入点云密度
- `max_dist_sq` 决定匹配时能接受多远的点对

这三者需要一起看。地图太密、当前点云太稀，或者拒绝门限过小，都可能导致配准不收敛。

## 推荐启动方式

```bash
ros2 launch small_gicp_relocalization small_gicp_relocalization_launch.py
```

如果系统已有完整集成入口，更推荐由上层 bringup 托管。

## 使用边界

- 它不是主里程计，不应该直接替代 LIO
- 它更适合在已有先验地图的场景下提供全局校正
- 如果地图质量不足或当前局部点云太稀疏，重定位结果会不稳定

## 调试重点

- 首先确认 `prior_pcd_file` 实际存在且地图坐标系语义正确
- 其次确认输入点云话题是否真的是世界系配准点云，而不是原始雷达点云
- 如果重定位结果跳变，优先检查初值、地图密度和 TF 链，而不是只改线程数

## 相关页面

- [定位模块总览](index.md)
- [LIO 总览](../lio/index.md)
- [Point-LIO](../lio/point_lio.md)

## 进一步阅读

- [small_gicp_relocalization README](https://github.com/Venom-Algorithm/Venom_VNV/blob/master/localization/relocalization/small_gicp_relocalization/README.md)
