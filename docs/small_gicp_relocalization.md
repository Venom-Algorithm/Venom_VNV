---
title: 重定位
desc: small_gicp_relocalization — 基于点云配准的全局重定位。
breadcrumb: 定位建图
layout: default
---

# small_gicp_relocalization

基于点云配准的重定位模块，用于机器人在已知地图中的全局定位。

## 功能

使用 small_gicp 算法进行点云对齐，计算 map 到 odom 的坐标变换，实现机器人的全局重定位。

## 快速开始

```bash
ros2 launch small_gicp_relocalization small_gicp_relocalization_launch.py
```

## 主要特性

- 基于 small_gicp 的快速点云配准
- 支持先验地图加载
- 实时计算 map→odom 变换
- 与 Point-LIO 无缝集成

## 详细文档

详见：[small_gicp_relocalization README](../relocalization/small_gicp_relocalization/README.md)
