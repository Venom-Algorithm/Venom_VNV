---
title: 仿真层
permalink: /simulation_overview
desc: 与真实部署链路解耦的仿真工作区与仿真基线总览。
breadcrumb: 模块与接口
layout: default
---

## 层级职责

仿真层负责：

- 在不接真实硬件的情况下验证定位、导航和系统流程
- 承载仿真世界、地图、模型和仿真专用 launch
- 作为算法回归和参数联调的独立环境

## 当前子项目

- [导航仿真工作区]({{ '/venom_nav_simulation' | relative_url }})

## 为什么单独成层

仿真工作区和真实部署工作区的依赖、资源文件和运行方式差异很大。

把仿真层单独拿出来，主要是为了：

1. 避免仿真资源污染主部署工作区
2. 保持导航/LIO 回归环境稳定
3. 让 Sim2Real 的边界更清楚

## 当前目录映射

- `simulation/venom_nav_simulation`

## 推荐使用方式

如果要验证：

- `MID360 + Gazebo + LIO + Nav2`
- 地图回归
- 参数联调

优先从仿真层进入，而不是把这些流程塞进 `venom_bringup` 主工作区。

## 相关页面

- [总体架构]({{ '/architecture' | relative_url }})
- [定位层]({{ '/localization_overview' | relative_url }})
- [规划层]({{ '/planning_overview' | relative_url }})
