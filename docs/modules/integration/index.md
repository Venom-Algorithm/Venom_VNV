---
title: 系统层
permalink: /integration_overview
desc: 启动编排、机器人描述、任务组织与整机模式入口总览。
breadcrumb: 模块与接口
layout: default
---

## 覆盖模块

- [系统启动]({{ '/venom_bringup' | relative_url }})
- [机器人描述]({{ '/venom_robot_description' | relative_url }})

## 层级职责

- `venom_bringup` 负责启动组合、场景模式与任务控制
- `venom_robot_description` 负责静态/动态 TF 发布
- 系统层负责把驱动、感知、定位、规划等模块组织成完整运行模式

## 为什么不叫“规划层”

系统层不是算法层。

- 它负责整机编排和任务组织
- 不负责局部/全局轨迹规划本身
- 类似 `ego_planner` 这类模块应进入 `planning/`

## 与其他模块的关系

- 向下组织驱动与算法模块
- 向上提供完整运行模式入口
