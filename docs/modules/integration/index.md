---
title: 系统集成
permalink: /integration_overview
desc: 启动编排、任务控制与机器人描述相关模块总览。
breadcrumb: 模块与接口
layout: default
---

## 覆盖模块

- [系统启动]({{ '/venom_bringup' | relative_url }})
- [机器人描述]({{ '/venom_robot_description' | relative_url }})

## 职责说明

- `venom_bringup` 负责启动组合、场景模式与任务控制
- `venom_robot_description` 负责静态/动态 TF 发布

## 与其他模块的关系

- 向下组织驱动与算法模块
- 向上提供完整运行模式入口
