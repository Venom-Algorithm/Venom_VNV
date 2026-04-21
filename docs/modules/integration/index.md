---
title: 系统层
permalink: /integration_overview
desc: 启动编排、机器人描述与整机模式入口总览。
breadcrumb: 模块与接口
layout: default
---

## 覆盖模块

- [系统启动]({{ '/venom_bringup' | relative_url }})
- [机器人描述]({{ '/venom_robot_description' | relative_url }})

## 层级职责

- `venom_bringup` 负责启动组合、场景模式与整机装配入口
- `venom_robot_description` 负责静态/动态 TF 发布
- 系统层负责把驱动、感知、定位、规划、任务等模块组织成完整运行模式

## 为什么不叫“规划层”

系统层不是算法层。

- 它负责整机编排和模式装配
- 不负责局部/全局轨迹规划本身
- 类似 `ego_planner` 这类模块应进入 `planning/`

## 为什么也不叫“任务层”

系统层不是行为树、waypoint 或监听器的归属层。

- `mission/` 负责任务流程和状态推进
- `system/` 负责把这些任务层与算法层装配成整机模式
- 后续不要继续把新任务包默认堆进 `venom_bringup`

## 与其他模块的关系

- 向下组织驱动与算法模块
- 向上提供完整运行模式入口
