---
title: 自瞄算法总览
desc: rm_auto_aim — 装甲板检测、目标跟踪、弹道解算与统一控制输出。
breadcrumb: 自瞄算法
layout: default
---

# rm_auto_aim

自瞄算法套件，包含装甲板检测、目标跟踪、弹道解算与统一控制输出。

## 子包结构

| 子包 | 功能 |
|------|------|
| `armor_detector` | 基于 YOLO 的装甲板检测 + PnP 解算 3D 位置 |
| `armor_tracker` | EKF 多目标跟踪，运动预测与补偿 |
| `auto_aim_solver` | 弹道解算，将跟踪结果转换为云台角度指令 |
| `auto_aim_interfaces` | 检测/跟踪/解算节点间的消息定义 |

## 数据流

```
/image_raw → armor_detector → /detector/armors → armor_tracker → /tracker/target → auto_aim_solver → /auto_aim → venom_serial_driver → C板
```

1. `armor_detector` — 订阅相机图像，识别装甲板，解算 3D 位置
2. `armor_tracker` — EKF 滤波跟踪，输出目标状态和预测位置
3. `auto_aim_solver` — 弹道解算，输出云台角度指令（pitch/yaw）和开火信号
4. `venom_serial_driver` — 订阅 `/auto_aim`，打包发送给 C 板

## 推荐启动方式

整套自瞄由 `venom_bringup` 统一托管：

```bash
# 自瞄测试（相机 + 自瞄 + 串口）
ros2 launch venom_bringup autoaim_test_bringup.launch.py

# 导航 + 自瞄（完整模式）
ros2 launch venom_bringup autoaim_nav_bringup.launch.py
```

## 子模块文档

- [armor_detector 详细文档](armor_detector.md)
- [armor_tracker 详细文档](armor_tracker.md)
- [armor_detector README](../rm_auto_aim/armor_detector/README.md)
- [armor_tracker README](../rm_auto_aim/armor_tracker/README.md)
