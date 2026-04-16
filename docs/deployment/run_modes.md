---
title: 运行模式
permalink: /run_modes
desc: 不同 bringup 模式的适用场景与输入输出关系。
breadcrumb: 部署与使用
layout: default
---

## 建图模式

- 入口：`mapping_bringup.launch.py`
- 目标：建立局部或全局地图
- 依赖：Livox、Point-LIO、可选 rf2o

## 重定位模式

- 入口：`relocalization_bringup.launch.py`
- 目标：在已有地图上恢复全局位姿
- 依赖：Point-LIO + `small_gicp_relocalization`

## 自瞄测试模式

- 入口：`autoaim_test_bringup.launch.py`
- 目标：相机、自瞄、串口链路联调

## 导航 + 自瞄模式

- 入口：`autoaim_nav_bringup.launch.py`
- 目标：在完整系统内同时运行移动与打击链路

## 进一步阅读

- [系统启动]({{ '/venom_bringup' | relative_url }})
- [自瞄算法]({{ '/rm_auto_aim' | relative_url }})
