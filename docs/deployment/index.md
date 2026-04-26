---
title: 部署与使用
description: 环境准备、硬件配置、运行模式与系统级接口的入口。
---

## 阅读顺序

这一部分面向第一次部署和现场联调，建议按以下顺序阅读：

1. [环境准备](environment.md)：准备 Ubuntu、ROS 2 Humble、rosdep、VS Code、远程桌面与常用开发工具
2. [雷达配置](lidar_setup.md)：安装 Livox-SDK2，配置 MID360 静态 IP、雷达参数和验证链路
3. [启动使用](../home/launch_usage.md)：查看常用 build、重编译、测试 launch 与整机启动命令

## 硬件链路

- [RealSense 配置](realsense_setup.md)：D435i / RealSense SDK 与 ROS wrapper 配置
- [底盘 CAN 部署](chassis_can_setup.md)：Scout / Hunter 等底盘 CAN 适配器配置
- [机械臂 CAN 部署](piper_can_setup.md)：Piper 机械臂 CAN 设备识别、命名与启动前检查
- [rc.local](rc_local.md)：开机自启动、静态路由与网络优先级设置

## 运行与接口

- [运行模式](run_modes.md)：不同联调、测试与整机模式下的使用方式
- [话题与 TF 总览](system_overview.md)：系统级话题接口与核心 TF 约定

如果你需要查看每个 package 的接口和参数，继续阅读 [模块与接口](../modules/index.md)。
