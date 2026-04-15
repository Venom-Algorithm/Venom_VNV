---
title: Point-LIO
desc: Point-LIO — MID360 参数与接口说明。
breadcrumb: 定位建图
layout: default
---

## 模块定位

`Point-LIO` 是当前系统的主激光惯性里程计模块，负责：

- 订阅 `/livox/lidar` 与 `/livox/imu`
- 输出 `/odom`
- 发布 `odom -> base_link`
- 输出 `/cloud_registered`
- 输出 `/cloud_registered_body`
- 输出 `/map_cloud`

当前仓库中的 `Point-LIO` 只保留 `MID360` 这一种硬件配置。

## 当前使用的配置文件

- 子模块配置：[mid360.yaml](/Users/liyh/venom_vnv/lio/Point-LIO/config/mid360.yaml)
- 建图配置：[mid360_mapping.yaml](/Users/liyh/venom_vnv/lio/Point-LIO/config/mid360_mapping.yaml)

## 参数说明

| 参数名 | 作用 | 默认值 |
| --- | --- | --- |
| `use_imu_as_input` | 控制 Point-LIO 使用哪一套状态传播主线。当前项目固定使用默认输出状态分支，不切到 IMU 输入分支。 | `False` |
| `prop_at_freq_of_imu` | 控制状态传播是否尽量跟随 IMU 的高频时间节奏执行。开启后，系统会按 IMU 更细粒度地传播状态。 | `True` |
| `check_satu` | 控制是否屏蔽接近 IMU 饱和上限的测量维度，避免加速度计或陀螺仪接近满量程时污染状态更新。 | `True` |
| `init_map_size` | 控制系统在正式进入建图与配准前，至少要累积多少初始地图点。值越大，启动更慢，但初始地图更稳。 | `100` |
| `point_filter_num` | 控制预处理阶段对原始点云按顺序抽样的步长。值越大，输入点数越少，计算量越低。 | `3` |
| `space_down_sample` | 控制是否在当前帧进入配准前做体素降采样。关闭后会保留更多点，但计算量明显增加。 | `True` |
| `filter_size_surf` | 控制当前帧点云的体素降采样尺寸。值越小，当前帧细节越多；值越大，匹配更轻量。 | `0.2` |
| `filter_size_map_internal` | 控制内部在线地图的体素尺度。这个参数会直接影响在线配准、匹配邻域密度和 odom 稳定性。 | `0.5` |
| `filter_size_map_publish` | 控制 `/map_cloud` 可视化地图的体素尺度。它只影响可视化地图的稀疏程度和发布负载，不参与内部配准。 | `0.8` |
| `filter_size_map_save` | 控制导出 PCD 时使用的体素尺度，只影响最终保存出来的地图密度。 | `0.2` |
| `ivox_nearby_type` | 控制 iVox 搜索邻域模式，决定配准时从周围多少体素中寻找邻居点。 | `6` |
| `runtime_pos_log_enable` | 控制是否输出运行时位姿日志，主要用于调试与离线分析。 | `False` |
| `common.lid_topic` | Point-LIO 订阅的 LiDAR 点云话题。 | `"livox/lidar"` |
| `common.imu_topic` | Point-LIO 订阅的 IMU 话题。 | `"livox/imu"` |
| `common.con_frame` | 控制是否把多帧 LiDAR 数据合并后再处理。 | `False` |
| `common.con_frame_num` | 当启用合帧时，指定合并的帧数。 | `1` |
| `common.cut_frame` | 控制是否把一帧 LiDAR 数据切成多个时间更短的子帧。 | `False` |
| `common.cut_frame_time_interval` | 当启用切帧时，指定每个子帧的时间长度。 | `0.1` |
| `common.time_diff_lidar_to_imu` | 指定 LiDAR 到 IMU 的固定时间偏移，用于时间对齐。 | `0.0` |
| `preprocess.lidar_type` | 指定 LiDAR 类型。当前 MID360 配置固定为 Livox 类型。 | `1` |
| `preprocess.scan_line` | 指定 LiDAR 线数配置。 | `4` |
| `preprocess.timestamp_unit` | 指定点时间戳单位。对 MID360 当前配置使用纳秒标记。 | `3` |
| `preprocess.blind` | 指定盲区距离，小于该距离的点会被丢弃。 | `0.5` |
| `mapping.imu_en` | 控制是否启用 IMU 参与 Point-LIO 状态估计。 | `True` |
| `mapping.extrinsic_est_en` | 控制是否在线估计 LiDAR 到 IMU 的外参。当前项目固定关闭。 | `False` |
| `mapping.imu_time_inte` | IMU 名义采样周期。 | `0.005` |
| `mapping.lidar_time_inte` | LiDAR 名义帧周期。 | `0.1` |
| `mapping.satu_acc` | IMU 加速度饱和阈值，用于测量维度屏蔽。 | `3.0` |
| `mapping.satu_gyro` | IMU 角速度饱和阈值，用于测量维度屏蔽。 | `35.0` |
| `mapping.acc_norm` | IMU 加速度单位对应的重力模长。使用 g 为单位时取 `1.0`。 | `1.0` |
| `mapping.lidar_meas_cov` | LiDAR 观测约束协方差。 | `0.01` |
| `mapping.acc_cov_output` | 输出状态模型中的加速度过程协方差。 | `500.0` |
| `mapping.gyr_cov_output` | 输出状态模型中的角速度过程协方差。 | `1000.0` |
| `mapping.b_acc_cov` | 加速度计零偏随机游走协方差。 | `0.0001` |
| `mapping.b_gyr_cov` | 陀螺仪零偏随机游走协方差。 | `0.0001` |
| `mapping.imu_meas_acc_cov` | IMU 加速度观测协方差。 | `0.01` |
| `mapping.imu_meas_omg_cov` | IMU 角速度观测协方差。 | `0.01` |
| `mapping.gyr_cov_input` | IMU 输入状态模型中的陀螺仪过程协方差。 | `0.01` |
| `mapping.acc_cov_input` | IMU 输入状态模型中的加速度过程协方差。 | `0.1` |
| `mapping.plane_thr` | 局部平面判定阈值。值越小，对平面更严格。 | `0.1` |
| `mapping.match_s` | 配准阶段的匹配搜索尺度参数。 | `81.0` |
| `mapping.ivox_grid_resolution` | iVox 地图网格分辨率。 | `2.0` |
| `mapping.gravity` | 估计器内部使用的重力向量。 | `[0.0, 0.0, -9.810]` |
| `mapping.gravity_init` | 启动阶段使用的初始重力猜测。 | `[0.0, 0.0, -9.810]` |
| `mapping.extrinsic_T` | LiDAR 在 IMU / 机体系下的平移外参。 | `[-0.011, -0.02329, 0.04412]` |
| `mapping.extrinsic_R` | LiDAR 在 IMU / 机体系下的旋转外参，按 3x3 旋转矩阵展开。 | `[[1,0,0],[0,1,0],[0,0,1]]` |
| `odometry.publish_odometry_without_downsample` | 控制是否在未完成当前帧降采样前就提前发布里程计。 | `False` |
| `odometry.enable_2d_mode` | 控制是否强制使用二维平面运动约束。 | `False` |
| `publish.path_en` | 控制是否发布路径消息。 | `True` |
| `publish.scan_publish_en` | 控制是否发布配准后的世界系点云。 | `True` |
| `publish.scan_bodyframe_pub_en` | 控制是否发布机体系点云。 | `False` |
| `publish.map_publish_en` | 控制是否默认发布累计地图点云。关闭后内部配准地图仍然存在，只是不再发布 `/map_cloud`。 | `True` |
| `publish.map_publish_interval` | 控制累计地图发布的帧间隔。值越大，`/map_cloud` 更新越慢、负载越低。 | `20` |
| `publish.tf_send_en` | 控制是否广播 `odom -> base_link` TF。 | `True` |
| `publish.odom_topic` | 控制 odometry 输出话题名。 | `"odom"` |
| `publish.cloud_registered_topic` | 控制世界系配准点云输出话题名。 | `"cloud_registered"` |
| `publish.cloud_registered_body_topic` | 控制机体系配准点云输出话题名。 | `"cloud_registered_body"` |
| `publish.map_topic` | 控制累计地图点云输出话题名。 | `"map_cloud"` |
| `publish.path_topic` | 控制路径输出话题名。 | `"path"` |
| `frame.odom_frame_id` | 控制 odometry 与 TF 父坐标系 frame id。 | `"odom"` |
| `frame.base_frame_id` | 控制机器人机体系 frame id。 | `"base_link"` |
| `frame.cloud_registered_frame_id` | 控制世界系配准点云 frame id。 | `"odom"` |
| `frame.cloud_registered_body_frame_id` | 控制机体系配准点云 frame id。 | `"base_link"` |
| `frame.map_frame_id` | 控制累计地图点云 frame id。 | `"odom"` |
| `pcd_save.pcd_save_en` | 控制是否启用 PCD 导出功能。开启后，导图数据来自内部在线地图，而不是来自 `/map_cloud`。 | `False` |
| `pcd_save.save_on_shutdown` | 控制是否在节点退出时自动保存一次 PCD。按 `Ctrl+C` 正常退出时也会触发。 | `True` |
| `pcd_save.save_period_sec` | 控制是否按固定秒数周期性保存 PCD。设为 `0.0` 表示关闭周期保存。 | `0.0` |
| `pcd_save.save_path` | 控制导出的 PCD 文件路径。可以写相对路径，也可以写绝对路径。 | `"PCD/scans.pcd"` |

## 参数联动理解

这几个参数不是彼此独立的：

- `point_filter_num` 决定预处理阶段的输入点密度
- `filter_size_surf` 决定当前帧参与配准时的体素降采样密度
- `filter_size_map_internal` 决定内部在线地图的稀疏程度，并直接影响在线配准效果
- `filter_size_map_publish` 决定 `/map_cloud` 可视化地图的密度与刷新负载
- `filter_size_map_save` 决定导出 PCD 的地图密度
- `init_map_size` 决定启动阶段需要积累多少点后才进入正式建图

如果 `point_filter_num` 较大，同时 `filter_size_surf` 也较大，那么系统启动会更轻量，但当前帧配准信息会更稀。

## 进一步阅读

- [LIO 总体约束](lio_overview.md)
- [话题参考](topics.md)
- [TF 树](tf_tree.md)
