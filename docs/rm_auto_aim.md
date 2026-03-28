# rm_auto_aim

RoboMaster 装甲板自动瞄准系统，提供完整的视觉识别与跟踪解决方案。

## 功能

集成装甲板检测、目标跟踪和预测算法，实现高精度自动瞄准。

## 快速开始

```bash
ros2 launch rm_vision_bringup vision_bringup.launch.py
```

## 主要特性

- 基于深度学习的装甲板检测
- 扩展卡尔曼滤波目标跟踪
- 弹道预测与补偿
- 多目标管理

## 子模块

- [armor_detector](./armor_detector.md) - 装甲板检测
- [armor_tracker](./armor_tracker.md) - 目标跟踪
- [auto_aim_interfaces](../rm_auto_aim/auto_aim_interfaces/README.md) - 接口定义

## TF 坐标系

系统完整 TF 树见：[tf_tree.md](./tf_tree.md)

## 详细文档

详见：[rm_auto_aim README](../rm_auto_aim/README.md)
