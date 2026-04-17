---
title: 总体架构
permalink: /architecture
desc: 从系统层面理解感知、定位、决策与执行四层结构。
breadcrumb: 模块与接口
layout: default
---

## 四层结构

1. 感知层：`perception/rm_auto_aim` 与相机输入链路
2. 定位层：`localization/lio/*` 与 `localization/relocalization/*`
3. 决策层：`venom_bringup` Mission Controller 与模式编排
4. 执行层：底盘、机械臂、串口与 PX4 桥接接口

## 当前目录映射

| 层级 | 主要目录 | 说明 |
| --- | --- | --- |
| 感知层 | `driver/ros2_hik_camera` + `perception/rm_auto_aim` | 图像输入、检测、跟踪与解算 |
| 定位层 | `driver/livox_ros_driver2` + `localization/lio` + `localization/relocalization` | 雷达输入、LIO 与重定位 |
| 决策层 | `venom_bringup` | 整机 launch、模式切换、任务控制 |
| 执行层 | `driver/scout_ros2`、`driver/hunter_ros2`、`driver/piper_ros`、`driver/venom_serial_driver`、`driver/venom_px4_bridge` | 底盘、机械臂、串口和 PX4 接口 |

## 仿真子项目

主工作区之外，当前还维护一个独立仿真工作区：

- `simulation/venom_nav_simulation`

它主要用于：

- `MID360 + Gazebo + LIO + Nav2` 联调
- 参数回归和流程验证
- 在不接真实硬件的情况下提前验证定位与导航链路

## 建议阅读顺序

- [驱动层]({{ '/driver_overview' | relative_url }})
- [定位建图]({{ '/localization_overview' | relative_url }})
- [自瞄算法]({{ '/rm_auto_aim' | relative_url }})
- [系统集成]({{ '/integration_overview' | relative_url }})
