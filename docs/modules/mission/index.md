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

- `venom_eagle_planner`、`venom_teb_controller` 应进入 `planning/navigation/`
- `venom_waypoint`、`venom_nav_bt`、`venom_global_monitor` 应进入 `mission/navigation/`
- `venom_moveit_grasp` 应进入 `planning/manipulation/`
- `venom_grasp_mission` 应进入 `mission/manipulation/`

## 推荐包命名

- 导航任务入口：`venom_waypoint`
- 导航行为树：`venom_nav_bt`
- 全局状态监听：`venom_global_monitor`
- 任务调度与管理：`venom_mission_manager`
- 抓取任务流程：`venom_grasp_mission`

## 当前状态

当前主工作区已经创建 `mission/` 目录，并落地了 `navigation/` 与 `manipulation/` 两个占位子目录。

后续新增的行为树、waypoint、任务监听、任务发布一类包，统一归到这里，而不是继续塞进 `venom_bringup`。

## 相关页面

- [总体架构](../architecture.md)
- [规划层](../planning/index.md)
- [系统层](../integration/index.md)
