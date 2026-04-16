---
title: 底盘驱动
permalink: /chassis_driver
desc: scout_ros2 + ugv_sdk — Scout 系列底盘 ROS2 控制接口。
breadcrumb: 硬件驱动
layout: default
---

# 底盘驱动 (scout_ros2 + ugv_sdk)

Scout 系列底盘的 ROS2 控制接口，基于 ugv_sdk 实现 CAN 总线通信。

## 支持硬件

- Scout 2.0
- Scout Mini（麦轮 / 全向轮）
- 支持 V1 和 V2 协议（仅 CAN 接口）

## 快速开始

### CAN 适配器配置

更完整的部署步骤可参考：[底盘 CAN 部署]({{ '/chassis_can_setup' | relative_url }})

```bash
# 加载内核模块
sudo modprobe gs_usb

# 启动 CAN 设备
sudo ip link set can0 up type can bitrate 500000

# 验证
ifconfig -a | grep can
```

> `ugv_sdk/scripts/` 下提供了 `setup_can2usb.bash`（首次配置）和 `bringup_can2usb.bash`（每次重插后启动）。

### 启动底盘节点

```bash
ros2 launch scout_base scout_base.launch.py
```

### 键盘遥控

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

## 架构说明

```
用户应用 (ROS2 节点)
       ↓ cmd_vel
   scout_base (ROS2 封装)
       ↓ C++ API
    ugv_sdk (通信库)
       ↓ CAN 帧
   CAN 适配器 → 底盘控制器
```

ugv_sdk 分三层抽象：
1. **interface** — 定义 C++ API
2. **robot_base** — 实现各型号和协议版本
3. **mobile_robot** — 运行时多态接口

## ROS 2 话题

| 方向 | 话题 | 消息类型 | 说明 |
|------|------|----------|------|
| 订阅 | `/cmd_vel` | `geometry_msgs/Twist` | 底盘速度指令 |
| 发布 | `/odom` | `nav_msgs/Odometry` | 底盘里程计 |

## 故障排查

1. **CAN 通信不通** → `candump can0` 检查是否有数据
2. **底盘不动** → 检查遥控器是否在手动模式，急停是否释放
3. **CAN 日志记录** → `candump -l can0`，回放用 `canplayer -I <file>.log`

## 详细文档

- [scout_ros2 README](../driver/scout_ros2/README.md)
- [ugv_sdk README](../driver/ugv_sdk/README.md)
- [通信协议文档](../driver/ugv_sdk/docs/)（含多型号用户手册 PDF）
