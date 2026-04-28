---
title: 感知层
description: 图像输入、检测、识别、跟踪与目标语义输出相关模块总览。
---

## 层级职责

感知层负责把原始传感器数据转换成上层可直接使用的结构化目标信息。

在当前仓库里，感知层主要覆盖：

- 目标检测
- 条码 / 二维码识别
- 目标跟踪
- 自瞄链路中的视觉前端
- 通用 YOLO 2D 检测输出

## 当前目录映射

- `driver/ros2_hik_camera`
- `perception/rm_auto_aim`
- `perception/yolo_detector`
- `perception/zbar_ros`

## 当前模块

- [自瞄算法总览](../auto_aim/index.md)
- [装甲板检测](../auto_aim/armor_detector.md)
- [目标跟踪](../auto_aim/armor_tracker.md)
- [YOLO Detector](yolo_detector.md)
- [ZBar ROS](zbar_ros.md)

## 接口约束

后续接入新的感知算法时，建议遵守这几个约束：

1. 输入优先复用标准图像话题，例如 `/image_raw`、`/camera_info`
2. 输出消息应明确区分“检测结果”“跟踪结果”“控制结果”
3. 不把控制语义直接塞进纯检测消息
4. 如果某个模块是通用检测器，它不应耦合某个比赛任务的特定字段

## 模块关系

- `ros2_hik_camera` 提供图像与相机内参
- `yolo_detector` 提供通用 2D 检测结果
- `zbar_ros` 提供通用二维码 / 条码识别结果
- `armor_detector` 提供装甲板特化检测与 3D 解算
- `armor_tracker` 对检测结果做目标级状态管理
- `auto_aim_solver` 再把目标状态转换成控制量

## 推荐阅读顺序

1. [YOLO Detector](yolo_detector.md)
2. [ZBar ROS](zbar_ros.md)
3. [自瞄算法总览](../auto_aim/index.md)
4. [装甲板检测](../auto_aim/armor_detector.md)
5. [目标跟踪](../auto_aim/armor_tracker.md)

## 相关页面

- [海康相机驱动](../drivers/ros2_hik_camera.md)
- [话题参考](../standards/topics.md)
