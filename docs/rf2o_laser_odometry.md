---
title: rf2o 激光里程计
desc: rf2o_laser_odometry — 基于距离流方法的 2D 激光扫描里程计。
breadcrumb: 定位建图
layout: default
---

## 模块定位

`rf2o_laser_odometry` 是轻量级 2D 激光里程计模块，负责：

- 从连续 2D 激光扫描中估计平面运动
- 在平面场景中提供低开销运动估计
- 作为 3D LIO 的补充或替代方案

## 适用场景

- 机器人只关心平面运动
- 需要极低计算负载的里程计
- 作为主定位失效时的辅助方案

## 核心特点

- 不依赖显式特征提取
- 基于 range flow 做稠密对齐
- 单核计算开销低
- 适合 2D 激光雷达场景

## 当前参数入口

当前仓库里最直接的启动入口是：

- [`rf2o_laser_odometry.launch.py`](/Users/liyh/venom_vnv/lio/rf2o_laser_odometry/launch/rf2o_laser_odometry.launch.py)

这个 launch 里已经直接写入了常用运行参数。

## 参数说明

| 参数名 | 作用 | 默认值 |
| --- | --- | --- |
| `laser_scan_topic` | 2D 激光扫描输入话题。 | `"/scan"` |
| `odom_topic` | 里程计输出话题。 | `"/odom_rf2o"` |
| `publish_tf` | 是否广播 TF。开启后会发布 `odom -> base_link`。 | `True` |
| `base_frame_id` | 机器人机体系 frame id。 | `"base_link"` |
| `odom_frame_id` | 里程计父坐标系 frame id。 | `"odom"` |
| `init_pose_from_topic` | 初始位姿输入话题。留空表示不从外部注入初值。 | `""` |
| `freq` | 主循环频率，单位 Hz。 | `20.0` |

## 推荐启动方式

```bash
ros2 launch rf2o_laser_odometry rf2o_laser_odometry.launch.py
```

## 与 LIO 的关系

在当前系统里，它更像是“互补定位模块”，而不是取代 3D LIO：

- [Point-LIO](point_lio.md) / [Fast-LIO](fast_lio.md)：主 3D 激光惯性里程计
- `rf2o_laser_odometry`：平面场景下的轻量补充

## 调试重点

- 没有输出时，先检查 `/scan` 是否稳定
- TF 冲突时，先确认是否已经有别的节点在发布 `odom -> base_link`
- 如果平面运动正常但结果漂移大，优先检查激光安装姿态和 scan 质量，而不是先把频率调高

## 相关页面

- [定位模块总览](localization_overview.md)
- [LIO 总览](lio_overview.md)

## 进一步阅读

- [rf2o_laser_odometry README](../lio/rf2o_laser_odometry/README.md)
