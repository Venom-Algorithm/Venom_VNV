---
title: 模块与接口
description: 系统模块的总体框架、分类约束与子文档入口。
---

## 总体框架

这一部分是整个系统的模块与接口总入口，阅读顺序建议是：

1. 先看 [总体架构](architecture.md)
2. 再按层级进入某个模块大类，例如 [驱动层](drivers/index.md)、[感知层](perception/index.md)、[定位层](localization/index.md)
3. 最后查看各个子算法、子包或子工作区的具体页面

## 分类入口

模块首页只放一级架构入口。具体算法、子包和工作区页面从对应分类页继续进入。

- [总体架构](architecture.md)
- [驱动层](drivers/index.md)
- [感知层](perception/index.md)
- [定位层](localization/index.md)
- [规划层](planning/index.md)
- [任务层](mission/index.md)
- [系统层](integration/index.md)
- [仿真层](simulation/index.md)

## 接口规范

- [话题参考](standards/topics.md)
- [TF 树](standards/tf_tree.md)

## 模块文档组织方式

每个模块分类页应尽量回答三件事：

1. 这一类模块在系统中的职责是什么
2. 这一类模块需要遵守哪些统一约束
3. 这一类模块下面有哪些具体实现与子文档

## 当前推荐的层级

1. `driver/`：硬件接入与桥接
2. `perception/`：检测、识别、跟踪等感知算法
3. `localization/`：LIO、里程计、重定位
4. `planning/`：导航规划、controller、机械臂运动规划
5. `mission/`：行为树、waypoint、监听器与任务调度
6. `system/`：系统启动、机器人描述与整机装配
7. `simulation/`：独立仿真工作区和仿真基线

## 进一步阅读

- [系统启动](integration/venom_bringup.md)
- [话题与 TF 总览](../deployment/system_overview.md)
