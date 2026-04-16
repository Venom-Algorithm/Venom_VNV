---
title: 话题与 TF 总览
permalink: /system_overview
desc: 系统级 topic map、TF 关系与关键数据流。
breadcrumb: 部署与使用
layout: default
---

## 适合什么时候看

- 想快速理解模块之间如何连起来
- 想查某条 topic 从哪来、到哪去
- 想排查 TF 缺失或坐标链不对

## 文档入口

- [话题参考]({{ '/topics' | relative_url }})
- [TF 树]({{ '/tf_tree' | relative_url }})

## 关键链路

- 感知链：相机 -> 检测 -> 跟踪 -> 弹道 -> 串口
- 定位链：Livox -> Point-LIO -> odom
- 重定位链：点云对齐 -> `map -> odom`
- 执行链：导航 / 自瞄控制 -> 串口 -> C 板
