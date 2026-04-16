---
title: 总体架构
permalink: /architecture
desc: 从系统层面理解感知、定位、决策与执行四层结构。
breadcrumb: 模块与接口
layout: default
---

## 四层结构

1. 感知层：相机与装甲板识别
2. 定位层：Point-LIO、rf2o、重定位
3. 决策层：`venom_bringup` Mission Controller
4. 执行层：底盘驱动与串口控制

## 建议阅读顺序

- [驱动层]({{ '/driver_overview' | relative_url }})
- [定位建图]({{ '/localization_overview' | relative_url }})
- [自瞄算法]({{ '/rm_auto_aim' | relative_url }})
- [系统集成]({{ '/integration_overview' | relative_url }})
