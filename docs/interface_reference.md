---
title: 模块与接口
desc: 系统模块的总体框架、分类约束与子文档入口。
breadcrumb: 模块与接口
layout: default
---

## 总体框架

这一部分是整个系统的模块与接口总入口，阅读顺序建议是：

1. 先看 [总体架构](architecture.md)
2. 再进入某个模块大类，例如 [驱动层](driver_overview.md)、[LIO](lio_overview.md)、[自瞄算法](rm_auto_aim.md)
3. 最后查看各个子算法或子包的具体页面

## 分类入口

- [驱动层](driver_overview.md)
- [LIO](lio_overview.md)
- [定位建图](localization_overview.md)
- [自瞄算法](rm_auto_aim.md)
- [系统集成](integration_overview.md)

## 接口规范

- [话题参考](topics.md)
- [TF 树](tf_tree.md)

## 模块文档组织方式

每个模块分类页应尽量回答三件事：

1. 这一类模块在系统中的职责是什么
2. 这一类模块需要遵守哪些统一约束
3. 这一类模块下面有哪些具体实现与子文档

## 进一步阅读

- [系统启动](venom_bringup.md)
- [话题与 TF 总览](system_overview.md)
