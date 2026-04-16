---
title: Fast-LIO
permalink: /fast_lio
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

## 当前使用的配置文件

- 子模块配置：[mid360.yaml](/Users/liyh/venom_vnv/lio/Fast-LIO/config/mid360.yaml)

## 参数说明

| 参数名 | 作用 | 默认值 |
| --- | --- | --- |
| `feature_extract_enable` | 是否启用特征提取前端。当前 MID360 配置保持关闭，直接走原始点到地图的配准流程。 | `false` |
| `point_filter_num` | 预处理阶段按顺序抽点的步长。值越大，进入配准的点越少。 | `3` |
| `max_iteration` | 每帧 scan-to-map 的最大迭代次数。增大后可能更稳，但单帧耗时更高。 | `3` |
| `filter_size_surf` | 当前帧点云降采样体素尺寸，单位米。越小保留细节越多，计算越重。 | `0.2` |
| `filter_size_map_internal` | 内部 `ikd-tree` 在线地图的体素尺寸，单位米。这个参数直接影响 odom 配准效果。 | `0.5` |
| `filter_size_map_publish` | `/map_cloud` 可视化地图的体素尺寸，单位米。只影响可视化密度与发布负载。 | `0.8` |
| `filter_size_map_save` | 导出 PCD 时的体素尺寸，单位米。只影响最终保存的地图密度。 | `0.2` |
| `cube_side_length` | 局部地图维护区域边长，单位米。值越大，保留的在线地图范围越大，内存与检索负担也更高。 | `1000.0` |
| `runtime_pos_log_enable` | 是否写出运行期位姿日志。主要用于离线分析，不建议默认开启。 | `false` |
| `common.lid_topic` | LiDAR 输入话题名。 | `"/livox/lidar"` |
| `common.imu_topic` | IMU 输入话题名。 | `"/livox/imu"` |
| `common.time_sync_en` | 是否启用软件时间同步。只有外部硬同步不可用时才建议打开。 | `false` |
| `common.time_offset_lidar_to_imu` | LiDAR 相对 IMU 的固定时间偏移，单位秒。已知标定值时可填写，否则保持 `0.0`。 | `0.0` |
| `preprocess.lidar_type` | 输入雷达类型选择。当前 MID360 固定使用 Livox 类型。 | `1` |
| `preprocess.scan_line` | 雷达线数配置。 | `4` |
| `preprocess.blind` | 盲区距离，单位米。小于该距离的点会被过滤。 | `0.5` |
| `preprocess.timestamp_unit` | 点时间戳单位。`3` 表示纳秒。 | `3` |
| `preprocess.scan_rate` | 雷达标称帧率，单位 Hz。用于预处理时的时间建模。 | `10` |
| `mapping.acc_cov` | IMU 加速度噪声协方差。值越大，滤波器越不信任加速度测量。 | `0.1` |
| `mapping.gyr_cov` | IMU 角速度噪声协方差。值越大，滤波器越不信任陀螺仪测量。 | `0.1` |
| `mapping.b_acc_cov` | 加速度计零偏随机游走协方差。 | `0.0001` |
| `mapping.b_gyr_cov` | 陀螺仪零偏随机游走协方差。 | `0.0001` |
| `mapping.fov_degree` | 视场角假设，单位度。局部地图裁剪和可见区域判断会用到。 | `360.0` |
| `mapping.det_range` | 有效探测距离，单位米。过远点不参与在线地图维护。 | `100.0` |
| `mapping.extrinsic_est_en` | 是否在线估计 LiDAR 到 IMU 外参。当前默认开启，但如果外参已经稳定，也可以固定下来。 | `true` |
| `mapping.extrinsic_T` | LiDAR 在 IMU / 机体系下的平移外参，单位米。 | `[-0.011, -0.02329, 0.04412]` |
| `mapping.extrinsic_R` | LiDAR 在 IMU / 机体系下的旋转外参，按 3x3 旋转矩阵展开。 | `[[1,0,0],[0,1,0],[0,0,1]]` |
| `publish.path_en` | 是否发布路径消息。 | `true` |
| `publish.effect_map_en` | 是否发布内部 effect map 调试结果。当前工程默认关闭。 | `false` |
| `publish.map_en` | 是否发布累计地图 `/map_cloud`。关闭后内部在线地图仍继续用于配准。 | `true` |
| `publish.scan_publish_en` | 是否发布世界系配准点云 `/cloud_registered`。 | `true` |
| `publish.dense_publish_en` | 是否发布更密的世界系点云。开启后带宽和 CPU 压力都会增大。 | `false` |
| `publish.scan_bodyframe_pub_en` | 是否发布机体系配准点云 `/cloud_registered_body`。 | `false` |
| `publish.map_publish_interval` | 地图发布间隔，按帧计数。值越大，`/map_cloud` 更新越慢。 | `20` |
| `publish.tf_send_en` | 是否广播 `odom -> base_link` TF。 | `true` |
| `publish.odom_topic` | 里程计输出话题名。 | `"odom"` |
| `publish.cloud_registered_topic` | 世界系配准点云输出话题名。 | `"cloud_registered"` |
| `publish.cloud_registered_body_topic` | 机体系配准点云输出话题名。 | `"cloud_registered_body"` |
| `publish.map_topic` | 地图输出话题名。 | `"map_cloud"` |
| `publish.path_topic` | 路径输出话题名。 | `"path"` |
| `frame.odom_frame_id` | odometry 与 TF 的父坐标系。 | `"odom"` |
| `frame.base_frame_id` | 机器人机体系。 | `"base_link"` |
| `frame.cloud_registered_frame_id` | 世界系配准点云的 frame id。 | `"odom"` |
| `frame.cloud_registered_body_frame_id` | 机体系配准点云的 frame id。 | `"base_link"` |
| `frame.map_frame_id` | 地图点云的 frame id。 | `"odom"` |
| `pcd_save.pcd_save_en` | 是否启用 PCD 导图。导图数据来自内部 `ikd-tree`，不是 `/map_cloud`。 | `false` |
| `pcd_save.save_on_shutdown` | 是否在节点正常退出或 `Ctrl+C` 时自动保存一次 PCD。 | `true` |
| `pcd_save.save_period_sec` | 周期导图时间间隔，单位秒。`0.0` 表示关闭周期保存。 | `0.0` |
| `pcd_save.save_path` | 导出的 PCD 文件路径。 | `"PCD/scans.pcd"` |

## 参数联动理解

- `point_filter_num`、`filter_size_surf` 一起决定每帧参与配准的点密度
- `filter_size_map_internal` 直接决定内部地图稀疏度，因此会影响 odom 稳定性
- `filter_size_map_publish` 只控制 `/map_cloud` 的可视化负载，不参与匹配
- `filter_size_map_save` 只控制导出的 PCD 密度
- `max_iteration` 决定单帧 scan-to-map 求解的迭代上限，过高会明显增加延迟

## 相关文档

- [LIO 总览]({{ '/lio_overview' | relative_url }})
- [Point-LIO]({{ '/point_lio' | relative_url }})
