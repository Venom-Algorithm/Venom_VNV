---
title: PX4 Bridge
permalink: /venom_px4_bridge
desc: venom_px4_bridge — PX4 集成项目根目录，以及 bridge 包与 px4_msgs 的职责划分。
breadcrumb: 硬件驱动
layout: default
---

## 模块定位

`driver/venom_px4_bridge` 不是单个 ROS 包，而是一个 PX4 集成项目根目录。

当前内部包含两个核心部分：

- `px4_msgs/`：vendored 的 PX4 ROS 2 消息定义
- `venom_px4_bridge/`：VNV 自有的 PX4 桥接包

它的目标不是把 PX4 直接暴露成一堆原始 `/fmu/*` 细节，而是先在桥接层完成消息版本固定、DDS 探测和状态整理，再向上层提供稳定接口。

## 目录结构

```text
driver/venom_px4_bridge/
├── px4_msgs/
└── venom_px4_bridge/
```

其中：

- `px4_msgs` 负责和 PX4 固件版本对齐的消息定义
- `venom_px4_bridge` 负责桥接逻辑、探测逻辑和状态输出

## 当前范围

当前这部分主要覆盖：

- `px4_agent_monitor`
- `px4_status_adapter`
- `px4_agent_probe.launch.py`

当前桥接输出包括：

- `/px4_bridge/agent_status`
- `/px4_bridge/state`
- `/px4_bridge/odom`
- `/px4_bridge/health`

## 推荐使用方式

如果只是检查 DDS Agent 和 PX4 链路是否打通，优先从 `venom_bringup` 的探测入口启动：

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch venom_bringup px4_agent_probe.launch.py
```

如果只想编译 PX4 相关部分，可从工作区根目录执行：

```bash
source /opt/ros/humble/setup.bash
cd ~/venom_ws
colcon build --symlink-install --packages-up-to px4_msgs venom_px4_bridge venom_bringup
```

## 为什么要单独拆成一个项目根目录

这样做主要是为了隔离三类变化：

1. `px4_msgs` 的上游版本变化
2. DDS Agent 可用性与探测逻辑
3. VNV 自己的桥接接口与状态整理逻辑

上层 `bringup` 和任务层更应该依赖桥接后的接口，而不是直接耦合 PX4 原始话题。

## 相关文档

- [驱动层]({{ '/driver_overview' | relative_url }})
- [系统启动]({{ '/venom_bringup' | relative_url }})

## 进一步阅读

- [venom_px4_bridge README](/Users/liyh/venom_vnv/driver/venom_px4_bridge/README.md)
- [deployment.md](/Users/liyh/venom_vnv/driver/venom_px4_bridge/docs/deployment.md)
- [COMPATIBILITY.md](/Users/liyh/venom_vnv/driver/venom_px4_bridge/COMPATIBILITY.md)
