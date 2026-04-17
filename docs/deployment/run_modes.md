---
title: 运行模式
permalink: /run_modes
desc: 不同 bringup 模式的适用场景与输入输出关系。
breadcrumb: 部署与使用
layout: default
---

## 建图模式

- 入口：`scout_mini_mapping.launch.py` 或 `sentry_mapping.launch.py`
- 目标：建立 2D 导航地图，同时保持 Point-LIO 的 3D 里程计输出
- 依赖：Livox、Point-LIO、pointcloud_to_laserscan、slam_toolbox、Nav2

## 重定位模式

- 入口：`relocalization_bringup.launch.py`
- 目标：在已有地图上恢复全局位姿
- 依赖：Point-LIO + `small_gicp_relocalization`

## 自瞄测试模式

- 入口：`infantry_auto_aim.launch.py`
- 目标：相机、自瞄、串口链路联调

## PX4 探测模式

- 入口：`px4_agent_probe.launch.py`
- 目标：检查 Micro XRCE-DDS Agent 与 PX4 桥接链路是否打通

## 整机模式

- 入口：`robot_bringup.launch.py`
- 目标：通过统一入口选择对应平台的整机 launch 组合

## 进一步阅读

- [系统启动]({{ '/venom_bringup' | relative_url }})
- [自瞄算法]({{ '/rm_auto_aim' | relative_url }})
