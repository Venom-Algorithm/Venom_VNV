---
title: 任务层
description: 任务编排、行为树、状态监听、目标下发与任务执行相关模块的统一入口。
---

## 层级职责

任务层负责回答两个问题：

1. 当前系统要做什么
2. 这个任务由谁下发、谁监听、谁推进

它本身不负责底层轨迹优化，也不直接承担硬件接入。

## 推荐目录结构

任务层推荐统一使用：

```text
mission/
├── navigation/
└── manipulation/
```

其中当前最推荐的组织方式是：

```text
mission/
├── navigation/
│   ├── venom_waypoint/
│   ├── venom_nav_bt/
│   ├── venom_global_monitor/
│   └── venom_mission_manager/
└── manipulation/
    ├── venom_grasp_mission/
    └── venom_pick_place_manager/
```

## 与规划层的边界

- `planning/` 负责“怎么规划路径、轨迹、控制量”
- `mission/` 负责“什么时候发目标、如何切任务、如何根据状态推进流程”

这两个层级不要混在一起。

例如：

- `ego-planner-swarm`、`venom_teb_controller` 应进入 `planning/navigation/`
- `venom_waypoint`、`venom_nav_bt`、`venom_global_monitor` 应进入 `mission/navigation/`
- 机械臂运动规划包应进入 `planning/manipulation/`
- 机械臂抓取任务流程包应进入 `mission/manipulation/`

## 推荐包命名

- 导航任务入口：`venom_waypoint`
- 导航行为树：`venom_nav_bt`
- 全局状态监听：`venom_global_monitor`
- 任务调度与管理：`venom_mission_manager`
- 抓取任务流程：后续可按具体任务命名，例如 `venom_grasp_mission`

## 当前状态

当前主工作区已经创建 `mission/` 目录，并落地了 `navigation/` 与 `manipulation/` 两个预留子目录。

这两个目录当前只用于承接后续独立任务包，仓库里已经可运行的任务控制实现还在 `venom_bringup` 内：

| 当前实现 | 路径 | 作用 |
| --- | --- | --- |
| 多航点导航入口 | `venom_bringup/venom_bringup/multi_waypoint_commander.py` | 读取 `waypoints.yaml`，调用 Nav2 Simple Commander 的 `followWaypoints()` |
| 健康状态感知入口 | `venom_bringup/venom_bringup/health_aware_commander.py` | 在多航点任务基础上接入状态监听、返航与恢复逻辑 |
| 任务控制核心 | `venom_bringup/venom_bringup/mission_controller/` | 提供状态监控、任务状态管理和行为插件抽象 |
| 任务插件 | `venom_bringup/venom_bringup/plugins/` | 当前包含健康状态插件与导航任务插件 |
| 参数文件 | `venom_bringup/config/scout_mini/mission_config.yaml`、`venom_bringup/config/scout_mini/waypoints.yaml` | 当前 Scout Mini 任务控制示例配置 |

因此当前判断规则是：

1. 使用已有任务控制功能时，从 `venom_bringup` 的 launch 或 `multi_waypoint_commander` 进入
2. 新增独立任务包时，放进 `mission/navigation/` 或 `mission/manipulation/`
3. 如果未来把已有任务控制代码迁出 `venom_bringup`，必须同步迁移 launch、参数路径和文档链接

## 当前可用入口

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch venom_bringup health_aware_navigation.launch.py
```

或者直接运行 console script：

```bash
cd ~/venom_ws
source install/setup.bash
ros2 run venom_bringup multi_waypoint_commander
```

## 相关页面

- [总体架构](../architecture.md)
- [规划层](../planning/index.md)
- [系统层](../integration/index.md)
