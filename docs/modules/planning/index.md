---
title: 规划层
description: 导航规划、controller 与机械臂运动规划相关模块总览。
---

## 层级职责

规划层负责：

- 根据目标点、地图、障碍物和当前状态生成可执行路径
- 输出局部轨迹、全局路径或控制量
- 处理避障、轨迹平滑和可行性约束
- 为抓取等任务生成可执行机械臂运动规划

它不负责：

- 原始传感器接入
- 纯定位估计
- waypoint、行为树和任务调度

## 推荐目录名称

这一层推荐统一使用：

```text
planning/
```

`ego-planner-swarm`、`venom_teb_controller`、自制 Nav2 controller、MoveIt 抓取规划这类模块，统一归到这一层。

## 当前状态

当前主工作区已经创建 `planning/` 目录，并在 `navigation/` 下接入了 `ego-planner-swarm` 和 `venom_teb_controller` 两个子模块。`manipulation/` 仍作为机械臂运动规划入口保留。

当前采用的组织方式例如：

```text
planning/
├── navigation/
│   ├── ego-planner-swarm/
│   ├── venom_teb_controller/
│   └── venom_nav_controller_xxx/
└── manipulation/
    └── venom_moveit_grasp/
```

## 接口约束

规划模块必须把这几类接口分清楚：

1. 输入清晰区分状态输入、地图输入和目标输入
2. 输出清晰区分“路径”“轨迹”“控制命令”
3. 不把任务决策逻辑和规划算法耦合在同一个包里
4. 与任务层和系统层的关系应是“被调用”，而不是“承担任务调度”

## 与任务层的边界

- `planning/` 负责“怎么走”
- `mission/` 负责“什么时候发目标、切换任务、推进流程”

这两个层级不要混在一起。

## 当前模块与预留入口

- `ego-planner-swarm`
- `venom_teb_controller`
- `venom_nav_controller_xxx`
- `venom_moveit_grasp`

## 相关页面

- [总体架构](../architecture.md)
- [Ego Planner Swarm](ego_planner_swarm.md)
- [TEB Controller](venom_teb_controller.md)
- [任务层](../mission/index.md)
- [系统层](../integration/index.md)
- [仿真层](../simulation/index.md)
