---
title: YOLO Detector
description: yolo_detector - 基于 YOLO 的通用 2D 目标检测模块与消息定义。
---

## 模块定位

`perception/yolo_detector` 是一个通用 2D 目标检测模块集合，用于把图像直接转换成 YOLO 风格的检测框结果。

它当前不承担：

- 深度估计
- 三维位姿恢复
- 多目标跟踪
- 自瞄任务语义

所以它更适合作为通用视觉检测入口，而不是直接等同于 `rm_auto_aim` 这种任务化感知链路。

## 包结构

当前目录里实际包含两个 ROS 2 包：

| 包名 | 作用 |
| --- | --- |
| `yolo_detector` | Python 检测节点，负责加载 YOLO 模型、订阅图像并发布检测结果 |
| `yolo_interfaces` | 检测结果消息定义，提供检测框、类别和整帧检测输出 |

对应代码入口：

- 节点实现：[yolo_node.py](https://github.com/Venom-Algorithm/Venom_VNV/blob/master/perception/yolo_detector/yolo_detector/yolo_node.py)
- launch 入口：[yolo_detector.launch.py](https://github.com/Venom-Algorithm/Venom_VNV/blob/master/perception/yolo_detector/launch/yolo_detector.launch.py)
- 默认参数：[yolo_detector.yaml](https://github.com/Venom-Algorithm/Venom_VNV/blob/master/perception/yolo_detector/config/yolo_detector.yaml)

## 数据流

```text
/image_raw
  -> yolo_detector
  -> /perception/detections
  -> 上层任务或可视化模块

/image_raw
  -> yolo_detector
  -> /perception/debug/yolo_result
  -> RViz / rqt_image_view
```

## 输入与输出

默认接口如下：

| 方向 | 话题 | 消息类型 | 说明 |
| --- | --- | --- | --- |
| 订阅 | `/image_raw` | `sensor_msgs/msg/Image` | 输入图像 |
| 发布 | `/perception/detections` | `yolo_interfaces/msg/YoloDetections` | 当前帧检测结果 |
| 发布 | `/perception/debug/yolo_result` | `sensor_msgs/msg/Image` | 叠加检测框后的调试图像 |

补充说明：

- `YoloDetections.header` 直接继承输入图像的 `header`
- `header.stamp` 会沿用图像时间戳
- `header.frame_id` 会沿用图像坐标系
- 当前节点不订阅 `camera_info`

## 消息定义

### `YoloBox.msg`

| 字段 | 作用 |
| --- | --- |
| `center_x` | 检测框中心点 x，单位为像素 |
| `center_y` | 检测框中心点 y，单位为像素 |
| `size_x` | 检测框宽度，单位为像素 |
| `size_y` | 检测框高度，单位为像素 |

当前使用的是像素坐标系下的 `xywh` 表示，而不是左上角加右下角。

### `YoloHypothesis.msg`

| 字段 | 作用 |
| --- | --- |
| `class_id` | 模型输出类别 id |
| `class_name` | 类别名称 |
| `score` | 置信度 |

### `YoloDetection.msg`

| 字段 | 作用 |
| --- | --- |
| `hypothesis` | 单个目标的类别信息 |
| `bbox` | 单个目标的 2D 检测框 |

### `YoloDetections.msg`

| 字段 | 作用 |
| --- | --- |
| `header` | 当前这一帧检测结果的时间戳和坐标系 |
| `detections` | 当前帧全部检测结果 |

## 参数说明

当前节点实际声明的参数如下：

| 参数名 | 作用 | 默认值 |
| --- | --- | --- |
| `detector_name` | 检测器名称字符串，主要用于标识当前节点配置。当前实现里不直接参与输出逻辑。 | `"yolo_detector"` |
| `model_path` | YOLO 模型路径，可以是本地 `.pt` 文件，也可以是 Ultralytics 可解析的模型名。 | `"yolov8n.pt"` |
| `image_topic` | 输入图像话题。 | `"/image_raw"` |
| `output_topic` | 检测结果输出话题。 | `"/perception/detections"` |
| `annotated_image_topic` | 调试图像输出话题。 | `"/perception/debug/yolo_result"` |
| `publish_annotated_image` | 是否发布叠加检测框后的调试图像。关闭后可以减少一部分带宽与 CPU 开销。 | `true` |
| `confidence_threshold` | 置信度阈值，传给 YOLO 推理接口。值越高，低分框越容易被过滤。 | `0.25` |
| `iou_threshold` | NMS 相关 IoU 阈值，传给 YOLO 推理接口。 | `0.45` |
| `device` | 推理设备字符串。留空时由 Ultralytics 自行选择；也可手动指定如 `cpu`、`0`。 | `""` |
| `class_ids` | 类别过滤列表，使用逗号分隔，例如 `0,2,5`。留空表示不过滤类别。 | `""` |

## Launch 参数

当前 launch 文件暴露了三个启动参数：

| Launch 参数 | 作用 | 默认值 |
| --- | --- | --- |
| `model_path` | 模型路径 | `"yolov8n.pt"` |
| `image_topic` | 输入图像话题 | `"/image_raw"` |
| `output_topic` | 检测结果输出话题 | `"/perception/detections"` |

需要注意：

- 当前 [yolo_detector.launch.py](https://github.com/Venom-Algorithm/Venom_VNV/blob/master/perception/yolo_detector/launch/yolo_detector.launch.py) 只把这三个参数传给节点
- `annotated_image_topic`、`publish_annotated_image`、`confidence_threshold`、`iou_threshold`、`device`、`class_ids` 虽然在节点里已经声明，但默认 launch 里没有单独暴露
- 如果你要临时改这些参数，可以用 `ros2 run ... --ros-args -p ...` 的方式传入，或者后续把 launch 再扩展

## 依赖与构建

这个模块运行时依赖：

- `rclpy`
- `sensor_msgs`
- `std_msgs`
- `cv_bridge`
- `ultralytics`
- `yolo_interfaces`

推荐先安装依赖：

```bash
cd ~/venom_ws
rosdep install -r --from-paths src --ignore-src --rosdistro $ROS_DISTRO -y
```

如果环境里的 `rosdep` 没有把 `ultralytics` 装好，可以手动补：

```bash
python3 -m pip install -U ultralytics
```

然后单独编译这两个包：

```bash
cd ~/venom_ws
colcon build --packages-select yolo_interfaces yolo_detector
source install/setup.bash
```

## 推荐启动方式

使用 launch：

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch yolo_detector yolo_detector.launch.py model_path:=/path/to/model.pt
```

直接运行节点：

```bash
cd ~/venom_ws
source install/setup.bash
ros2 run yolo_detector yolo_node
```

如果要直接覆盖更多参数，可以这样：

```bash
cd ~/venom_ws
source install/setup.bash
ros2 run yolo_detector yolo_node --ros-args \
  -p model_path:=/path/to/model.pt \
  -p image_topic:=/camera/image_raw \
  -p output_topic:=/perception/detections \
  -p publish_annotated_image:=false \
  -p confidence_threshold:=0.4 \
  -p class_ids:="0,1"
```

## 工程边界

`yolo_detector` 和 `rm_auto_aim` 的边界应保持清楚：

| 模块 | 负责内容 | 不负责内容 |
| --- | --- | --- |
| `yolo_detector` | 通用 2D 检测、类别与框输出 | 跟踪、弹道、自瞄控制 |
| `rm_auto_aim` | 目标检测、目标跟踪、弹道解算、控制输出 | 通用 YOLO 检测器抽象 |

如果后续要把 YOLO 检测接进任务系统，建议保持两层分离：

1. `yolo_detector` 只输出纯检测消息
2. 上层再做任务语义映射、筛选、跟踪或行为决策

## 适用场景

这个模块比较适合：

- 通用目标检测基线验证
- 无人机或无人车上的 2D 视觉前端
- 给后续任务层提供统一的纯检测输入
- 在不引入任务语义的前提下快速替换不同 YOLO 权重

## 相关页面

- [感知层](index.md)
- [海康相机驱动](../drivers/ros2_hik_camera.md)
- [自瞄算法总览](../auto_aim/index.md)
- [话题参考](../standards/topics.md)
