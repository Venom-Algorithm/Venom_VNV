---
title: Venom VNV
desc: 基于 ROS2 Humble 的 RoboMaster 机器人系统，集成定位建图、重定位、导航与自瞄能力。
breadcrumb: 首页
layout: default
---

## 系统架构

```
┌─────────────────────────────────────────────────────┐
│                   感知层 Perception                   │
│         海康相机 (ros2_hik_camera)                    │
│              ↓ /image_raw                            │
│     装甲板检测 (armor_detector) → 目标跟踪 (armor_tracker) │
│              ↓ /tracker/target                       │
│     弹道解算 (auto_aim_solver) → /auto_aim            │
├─────────────────────────────────────────────────────┤
│                   定位层 Localization                 │
│  Livox Mid360 (livox_ros_driver2)                    │
│       ↓ /livox/lidar                                 │
│  3D 里程计 (Point-LIO) ──→ 重定位 (small_gicp_reloc)  │
│  2D 里程计 (rf2o_laser_odometry)                      │
├─────────────────────────────────────────────────────┤
│                   决策层 Decision                     │
│  Mission Controller (venom_bringup)                   │
│  状态监控 · 任务中断恢复 · 插件化行为                   │
├─────────────────────────────────────────────────────┤
│                   执行层 Actuation                    │
│  串口通信 (venom_serial_driver) ←→ DJI C 板           │
│  底盘驱动 (scout_ros2 + ugv_sdk) ←→ Scout Mini       │
└─────────────────────────────────────────────────────┘
```

## 快速导航

<div class="card-grid">
  <a href="{{ '/setup' | relative_url }}" class="card" style="text-decoration:none">
    <h3>⚙️ 装配配置</h3>
    <p>从零开始搭建开发环境，安装 SDK、编译工作空间、配置硬件。</p>
  </a>
  <a href="{{ '/topics' | relative_url }}" class="card" style="text-decoration:none">
    <h3>📡 话题参考</h3>
    <p>系统级 ROS2 话题一览、数据流图、自定义消息字段。</p>
  </a>
  <a href="{{ '/rm_auto_aim' | relative_url }}" class="card" style="text-decoration:none">
    <h3>🎯 自瞄算法</h3>
    <p>装甲板检测 → EKF 跟踪 → 弹道解算 → 串口输出的完整流水线。</p>
  </a>
  <a href="{{ '/point_lio' | relative_url }}" class="card" style="text-decoration:none">
    <h3>📍 定位建图</h3>
    <p>Point-LIO 3D 里程计、rf2o 2D 里程计、small_gicp 重定位。</p>
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
| 📍 定位建图 | `rf2o_laser_odometry` | 2D 激光扫描里程计 |
| 📍 定位建图 | `small_gicp_relocalization` | 点云重定位 |
| 🎯 自瞄算法 | `rm_auto_aim` | 检测 + 跟踪 + 解算 + 消息定义 |
| 🔧 系统集成 | `venom_bringup` | 启动配置 + Mission Controller |
| 🔧 系统集成 | `venom_robot_description` | TF 树发布 |

## 快速开始

```bash
# 克隆主仓库及子模块
git clone --recurse-submodules git@github.com:Venom-Algorithm/Venom_VNV.git
cd Venom_VNV

# 安装依赖
rosdep install --from-paths . --ignore-src -r -y

# 编译
colcon build --symlink-install -DCMAKE_BUILD_TYPE=Release
```

> 详细的装配步骤见 [装配配置]({{ '/setup' | relative_url }})
