---
title: 规划层
permalink: /planning_overview
desc: 轨迹规划、局部避障、全局路径与运动生成相关模块的预留层。
breadcrumb: 模块与接口
layout: default
---

## 层级职责

规划层负责：

- 根据目标点、地图、障碍物和当前状态生成可执行路径
- 输出局部轨迹或全局路径
- 处理避障、轨迹平滑和可行性约束

它不负责：

- 原始传感器接入
- 纯定位估计
- 系统模式编排

## 推荐目录名称

这一层推荐统一使用：

```text
planning/
```

后续像 `ego_planner` 这类模块，建议直接归到这一层，而不是放进系统层或任务层。

## 当前状态

当前主工作区里还没有正式并入 `planning/` 目录下的模块，这一层先作为结构预留。

推荐未来的组织方式例如：

```text
planning/
├── ego_planner/
├── local_planner_xxx/
└── global_planner_xxx/
```

## 接口建议

后续规划模块建议遵守这几个方向：

1. 输入清晰区分状态输入、地图输入和目标输入
2. 输出清晰区分“路径”“轨迹”“控制命令”
3. 不把任务决策逻辑和规划算法耦合在同一个包里
4. 与系统层的关系应是“被编排”，而不是“承担系统编排”

## 与系统层的边界

- `planning/` 负责“怎么走”
- `system/` 负责“什么时候启动哪个模式”

这两个层级不要混在一起。

## 预期模块

- `ego_planner`
- 其他局部避障与轨迹生成算法

## 相关页面

- [总体架构]({{ '/architecture' | relative_url }})
- [系统层]({{ '/integration_overview' | relative_url }})
- [仿真层]({{ '/simulation_overview' | relative_url }})
