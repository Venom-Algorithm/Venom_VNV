---
title: Venom VNV
permalink: /
desc: 面向多类智能无人系统竞赛的通用平台，支持导航、抓取、自瞄与多载体系统集成。
breadcrumb: 首页
layout: default
---

## 项目定位

Venom VNV 是一个基于 ROS 2 Humble 构建的综合通用平台，面向：

- RoboMaster
- CUADC
- RoboTac
- 智能无人系统
- 机器人与人工智能等相关比赛

项目目标是提供一个尽可能到手即用的统一底座，用于支持：

- 导航
- 抓取
- 自瞄
- 无人车
- 无人机
- 无人船

通过统一的驱动层、定位层、任务控制层和接口层，降低不同赛事和不同平台之间的迁移成本。

## 快速导航

<div class="card-grid">
  <a href="{{ '/quick_start' | relative_url }}" class="card" style="text-decoration:none">
    <h3>⚙️ 快速开始</h3>
    <p>按标准流程拉取仓库、安装依赖并完成首次编译。</p>
  </a>
  <a href="{{ '/environment' | relative_url }}" class="card" style="text-decoration:none">
    <h3>🧰 环境配置</h3>
    <p>准备 Ubuntu、SSH、ROS、rosdep、VS Code、Clash 与 NoMachine。</p>
  </a>
  <a href="{{ '/lidar_setup' | relative_url }}" class="card" style="text-decoration:none">
    <h3>📡 配置雷达</h3>
    <p>安装 Livox-SDK2、配置 MID360 网络参数并验证雷达链路。</p>
  </a>
</div>

## 子模块一览

| 分类 | 子模块 | 说明 |
|------|--------|------|
| 🖥️ 硬件驱动 | `livox_ros_driver2` | Livox Mid360 激光雷达驱动 |
| 🖥️ 硬件驱动 | `ros2_hik_camera` | 海康 USB3.0 工业相机驱动 |
| 🖥️ 硬件驱动 | `scout_ros2` + `ugv_sdk` | Scout Mini 底盘驱动 |
| 🖥️ 硬件驱动 | `venom_serial_driver` | NUC ↔ DJI C 板串口通信 |
| 📍 定位建图 | `Point-LIO` | 高带宽激光惯性里程计 |
| 📍 定位建图 | `Fast-LIO` | FAST-LIO ROS2 版本 |
| 📍 定位建图 | `rf2o_laser_odometry` | 2D 激光扫描里程计 |
| 📍 定位建图 | `small_gicp_relocalization` | 点云重定位 |
| 🎯 自瞄算法 | `rm_auto_aim` | 检测 + 跟踪 + 解算 + 消息定义 |
| 🔧 系统集成 | `venom_bringup` | 启动配置 + Mission Controller |
| 🔧 系统集成 | `venom_robot_description` | TF 树发布 |
