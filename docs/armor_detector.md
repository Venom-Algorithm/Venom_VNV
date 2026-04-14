---
title: 装甲板检测
desc: armor_detector — 基于深度学习识别装甲板并解算 3D 位置。
breadcrumb: 自瞄算法
layout: default
---

# armor_detector

装甲板检测模块，基于深度学习识别装甲板并解算 3D 位置。

## 功能

订阅相机图像，识别装甲板目标，解算其在相机坐标系下的 3D 位置。

## 快速开始

```bash
ros2 launch armor_detector armor_detector.launch.py
```

## 主要特性

- 基于 YOLO 的装甲板检测
- PnP 算法解算 3D 位置
- 支持多种装甲板类型
- 实时性能优化

## 详细文档

详见：[armor_detector README](../rm_auto_aim/armor_detector/README.md)
