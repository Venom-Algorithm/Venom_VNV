---
title: 模块与接口
permalink: /interface_reference
desc: 系统模块的总体框架、分类约束与子文档入口。
breadcrumb: 模块与接口
layout: default
---

## 总体框架

这一部分是整个系统的模块与接口总入口，阅读顺序建议是：

1. 先看 [总体架构]({{ '/architecture' | relative_url }})
2. 再进入某个模块大类，例如 [驱动层]({{ '/driver_overview' | relative_url }})、[LIO]({{ '/lio_overview' | relative_url }})、[自瞄算法]({{ '/rm_auto_aim' | relative_url }})
3. 最后查看各个子算法或子包的具体页面

## 分类入口

- [驱动层]({{ '/driver_overview' | relative_url }})
- [LIO]({{ '/lio_overview' | relative_url }})
- [定位建图]({{ '/localization_overview' | relative_url }})
- [自瞄算法]({{ '/rm_auto_aim' | relative_url }})
- [系统集成]({{ '/integration_overview' | relative_url }})

## 接口规范

- [话题参考]({{ '/topics' | relative_url }})
- [TF 树]({{ '/tf_tree' | relative_url }})

## 模块文档组织方式

每个模块分类页应尽量回答三件事：

1. 这一类模块在系统中的职责是什么
2. 这一类模块需要遵守哪些统一约束
3. 这一类模块下面有哪些具体实现与子文档

## 进一步阅读

- [系统启动]({{ '/venom_bringup' | relative_url }})
- [话题与 TF 总览]({{ '/system_overview' | relative_url }})
