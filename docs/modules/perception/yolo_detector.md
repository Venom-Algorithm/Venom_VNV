---
title: YOLO Detector
permalink: /yolo_detector
desc: yolo_detector — 基于 YOLO 的通用 2D 目标检测模块与消息定义。
breadcrumb: 感知层
layout: default
---

## 模块定位

`perception/yolo_detector` 是一个通用 2D 目标检测模块集合，不绑定自瞄链路本身。

它当前包含两部分：

- `yolo_interfaces/`：YOLO 检测结果相关消息定义
- `yolo_detector/`：Python 检测节点

## 输入与输出

默认话题如下：

| 方向 | 话题 | 说明 |
| --- | --- | --- |
| 订阅 | `/image_raw` | 输入图像 |
| 发布 | `/perception/detections` | 当前帧检测结果 |
| 发布 | `/perception/debug/yolo_result` | 调试叠加图 |

## 消息结构

当前消息设计保持极简，主要服务于纯 2D 检测：

- `YoloBox.msg`：像素坐标系下的 `xywh`
- `YoloHypothesis.msg`：类别、类别名、置信度
- `YoloDetection.msg`：单个检测结果
- `YoloDetections.msg`：整帧检测结果数组

这套格式目前不包含：

- 深度
- 三维位姿
- 跟踪状态

如果后续要加这些能力，更适合新增消息，而不是污染当前这组纯检测接口。

## 当前参数入口

- [yolo_detector.yaml](/Users/liyh/venom_vnv/perception/yolo_detector/config/yolo_detector.yaml)
- [`yolo_node.py`](/Users/liyh/venom_vnv/perception/yolo_detector/yolo_detector/yolo_node.py)

## 依赖说明

这个模块依赖：

- `rclpy`
- `sensor_msgs`
- `cv_bridge`
- `yolo_interfaces`
- `ultralytics`

其中 `ultralytics` 由 `rosdep` 安装最稳妥；如果环境里没有配好 `rosdep`，可手动补：

```bash
python3 -m pip install -U ultralytics
```

## 推荐启动方式

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch yolo_detector yolo_detector.launch.py model_path:=/path/to/model.pt
```

或直接运行默认节点：

```bash
cd ~/venom_ws
source install/setup.bash
ros2 run yolo_detector yolo_node
```

## 与自瞄模块的关系

`yolo_detector` 和 `rm_auto_aim` 不应混为一谈：

- `yolo_detector` 是通用检测器
- `rm_auto_aim` 是带任务语义的完整感知与控制链路

前者适合做通用目标检测基线，后者适合做装甲板任务链路。

## 相关页面

- [感知层]({{ '/perception_overview' | relative_url }})
- [海康相机驱动]({{ '/ros2_hik_camera' | relative_url }})
- [自瞄算法总览]({{ '/rm_auto_aim' | relative_url }})
