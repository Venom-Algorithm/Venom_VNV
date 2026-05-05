---
title: 运行模式
description: 不同 bringup 模式的适用场景与输入输出关系。
---

## 建图模式

- 入口：`scout_mini_mapping.launch.py` 或 `sentry_mapping.launch.py`
- 目标：建立 2D 导航地图，同时保持 Point-LIO 的 3D 里程计输出
- 依赖：Livox、Point-LIO、pointcloud_to_laserscan、slam_toolbox、Nav2

## Point-LIO 纯里程计模式

- 入口：`mid360_point_lio_odom.launch.py`
- 目标：只保留高实时性 odom 与 TF 输出，关闭地图发布和 PCD 保存负载
- 默认配置：`venom_bringup/config/examples/point_lio_online_odom.yaml`

## Point-LIO 异步地图模式

- 入口：`mid360_point_lio_async_map.launch.py`
- 目标：保持里程计主线程实时，把地图发布 / PCD 相关工作放到异步地图线程
- 默认配置：`venom_bringup/config/examples/point_lio_online_async_map.yaml`

## Point-LIO 离线导图模式

- 入口：`mid360_point_lio_offline_map.launch.py`
- 目标：从 rosbag2 离线读取 `/livox/lidar` 和 `/livox/imu`，生成 PCD 地图
- 必填参数：`bag_path:=/absolute/path/to/rosbag2_dir`
- 输出参数：`output_pcd_path:=/absolute/path/to/offline_map.pcd`

## 重定位历史入口（暂停）

- 入口：`relocalization_bringup.launch.py`
- 状态：GICP 重定位当前因稳定性问题暂时下线
- 说明：入口文件保留作为后续恢复集成的历史入口，但新工作区默认不会拉取 `small_gicp_relocalization`

## 自瞄测试模式

- 入口：`infantry_auto_aim.launch.py`
- 目标：相机、自瞄、串口链路联调

## PX4 探测模式

- 入口：`px4_agent_probe.launch.py`
- 目标：检查 Micro XRCE-DDS Agent 与 PX4 桥接链路是否打通

## PX4 外部位姿桥接模式

- 入口：`px4_vps_bridge.launch.py`
- 目标：把上游 `nav_msgs/Odometry` 转成 PX4 可接收的 `VehicleOdometry`
- 默认输入：`/lio/vps/odometry`
- 默认输出：`/fmu/in/vehicle_visual_odometry`

## 任务控制模式

- 入口：`health_aware_navigation.launch.py`
- 目标：运行带状态监听、任务暂停 / 恢复和航点恢复能力的多航点导航
- 配置：`venom_bringup/config/scout_mini/mission_config.yaml`、`venom_bringup/config/scout_mini/waypoints.yaml`

## 整机模式

- 入口：`robot_bringup.launch.py`
- 目标：通过统一入口选择对应平台的整机 launch 组合
- 当前状态：顶层选择逻辑已存在，但各机器人子目录下的 `robot_bringup.launch.py` 模板尚未全部落地，日常联调优先使用上面列出的具体入口

## 进一步阅读

- [系统启动](../modules/integration/venom_bringup.md)
- [自瞄算法](../modules/auto_aim/index.md)
