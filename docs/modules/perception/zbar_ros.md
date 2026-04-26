---
title: ZBar ROS
description: zbar_ros - 基于 ZBar 的二维码 / 条码识别模块与结构化检测接口。
---

## 模块定位

`perception/zbar_ros` 是一个纯 2D 的二维码 / 条码识别模块集合，用于把图像直接转换成结构化识别结果。

它当前不承担：

- 深度估计
- 三维位姿恢复
- 目标跟踪
- 自瞄任务语义

因此它更接近通用视觉识别前端，而不是像 `rm_auto_aim` 那样的任务化感知链路。

## 包结构

当前目录里实际包含两个 ROS 2 包：

| 包名 | 作用 |
| --- | --- |
| `zbar_ros` | C++ 检测节点、调试图像发布与离线 dataset helper |
| `zbar_interfaces` | 条码识别结果消息定义 |

对应入口：

- 节点实现：[`barcode_reader_node.cpp`](https://github.com/Venom-Algorithm/Venom_VNV/blob/master/perception/zbar_ros/src/barcode_reader_node.cpp)
- launch 入口：[`zbar_ros.launch.py`](https://github.com/Venom-Algorithm/Venom_VNV/blob/master/perception/zbar_ros/launch/zbar_ros.launch.py)
- 离线验证 launch：[`dataset_barcode.launch.py`](https://github.com/Venom-Algorithm/Venom_VNV/blob/master/perception/zbar_ros/launch/dataset_barcode.launch.py)
- 包级 README：[`perception/zbar_ros/README.md`](https://github.com/Venom-Algorithm/Venom_VNV/blob/master/perception/zbar_ros/README.md)

## 数据流

```text
/image_raw
  -> zbar_ros
  -> /perception/barcodes
  -> 上层任务或可视化模块

/image_raw
  -> zbar_ros
  -> /perception/debug/barcodes
  -> RViz / rqt_image_view
```

## 输入与输出

默认接口如下：

| 方向 | 话题 | 消息类型 | 说明 |
| --- | --- | --- | --- |
| 订阅 | `/image_raw` | `sensor_msgs/msg/Image` | 输入图像 |
| 发布 | `/perception/barcodes` | `zbar_interfaces/msg/BarcodeDetections` | 当前帧识别结果 |
| 发布 | `/perception/debug/barcodes` | `sensor_msgs/msg/Image` | 叠加识别框后的调试图像 |

补充说明：

- `BarcodeDetections.header` 直接继承输入图像的 `header`
- `header.stamp` 会沿用图像时间戳
- `header.frame_id` 会沿用图像坐标系
- 当前节点不订阅 `/camera_info`

## TF 约束

`zbar_ros` 不发布任何 TF。

原因很直接：

- 当前输出只是图像平面上的识别结果
- 仅凭单目二维码 / 条码解码结果不能推出可靠的 3D 位姿
- 相机 frame 的所有权应继续留在上游驱动或 `venom_robot_description`

因此这里的正确做法是：

1. 保持识别消息继承源图像 `frame_id`
2. 不在这个模块里构造新的 `camera_*` 或 `target_*` TF
3. 如果后续要做码位姿估计，单独加一个 pose-estimation stage，并定义新的 TF 契约

## 消息定义

### `BarcodeDetection.msg`

| 字段 | 作用 |
| --- | --- |
| `data` | 解码后的字符串内容 |
| `symbology` | ZBar 识别到的码制名称，例如 `QRCODE` |
| `polygon` | 图像像素坐标系下的 2D 多边形轮廓 |

### `BarcodeDetections.msg`

| 字段 | 作用 |
| --- | --- |
| `header` | 当前帧识别结果的时间戳和坐标系 |
| `detections` | 当前帧全部识别结果 |

## 参数说明

当前检测节点实际声明的参数如下：

| 参数名 | 作用 | 默认值 |
| --- | --- | --- |
| `publish_debug_image` | 是否发布调试图像。关闭后可以减少一部分带宽与 CPU 开销。 | `true` |
| `qrcode_only` | 是否只识别 QR code。若关闭，则允许 ZBar 扫描更多条码类型。 | `true` |

## Launch 参数

### `zbar_ros.launch.py`

| Launch 参数 | 作用 | 默认值 |
| --- | --- | --- |
| `image_topic` | 输入图像话题 | `"/image_raw"` |
| `detections_topic` | 检测结果输出话题 | `"/perception/barcodes"` |
| `debug_image_topic` | 调试图像输出话题 | `"/perception/debug/barcodes"` |
| `publish_debug_image` | 是否发布调试图像 | `"true"` |
| `qrcode_only` | 是否只识别 QR code | `"true"` |

### `dataset_barcode.launch.py`

| Launch 参数 | 作用 | 默认值 |
| --- | --- | --- |
| `dataset_path` | 离线测试图片目录 | `share/zbar_ros/data/dataset` |
| `image_topic` | publisher 和 detector 共享的图像话题 | `"/perception/test/image_raw"` |
| `detections_topic` | 检测结果输出话题 | `"/perception/barcodes"` |
| `debug_image_topic` | 调试图像输出话题 | `"/perception/debug/barcodes"` |
| `frame_id` | 离线图片发布时写入的 frame id | `"dataset_camera_optical_frame"` |
| `publish_interval_seconds` | 图片发布周期 | `"1.0"` |
| `publish_debug_image` | 是否发布调试图像 | `"true"` |
| `qrcode_only` | 是否只识别 QR code | `"true"` |

需要注意：

- `dataset_camera_optical_frame` 只是离线测试 frame，不属于系统运行时 TF 树
- 真机接入时，`frame_id` 应由上游相机驱动决定，`zbar_ros` 只负责透传

## 依赖与构建

这个模块运行时依赖：

- `rclcpp`
- `sensor_msgs`
- `cv_bridge`
- `OpenCV`
- `zbar`
- `zbar_interfaces`

推荐先安装依赖：

```bash
cd ~/venom_ws
rosdep install -r --from-paths src --ignore-src --rosdistro $ROS_DISTRO -y
```

然后单独编译这两个包：

```bash
cd ~/venom_ws
colcon build --packages-select zbar_interfaces zbar_ros
source install/setup.bash
```

## 推荐启动方式

接入真实相机：

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch zbar_ros zbar_ros.launch.py
```

离线 dataset 验证：

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch zbar_ros dataset_barcode.launch.py
```

如果要覆盖相机话题，可以这样：

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch zbar_ros zbar_ros.launch.py image_topic:=/camera/image_raw
```

## 运行验收

建议至少检查这几项：

1. `colcon build --packages-select zbar_interfaces zbar_ros` 通过
2. `ros2 launch zbar_ros dataset_barcode.launch.py` 能正常拉起
3. `/perception/barcodes` 发布 `zbar_interfaces/msg/BarcodeDetections`
4. `/perception/debug/barcodes` 发布带标注的调试图像
5. `zbar_ros` 不发布任何 TF

## 工程边界

`zbar_ros` 的边界应保持清楚：

| 模块 | 负责内容 | 不负责内容 |
| --- | --- | --- |
| `zbar_ros` | 纯 2D 条码 / 二维码识别、结构化像素轮廓输出 | 位姿估计、TF 发布、目标跟踪、任务决策 |
| 上层任务模块 | 使用识别结果做筛选、关联、动作决策 | 不应反向要求 `zbar_ros` 塞入任务语义字段 |

如果后续真的需要码位姿，建议保持两层分离：

1. `zbar_ros` 继续只输出纯识别结果
2. 新增上层节点读取识别结果、相机内参与标定信息，再单独做 pose estimation

## 相关页面

- [感知层](index.md)
- [YOLO Detector](yolo_detector.md)
- [海康相机驱动](../drivers/ros2_hik_camera.md)
- [话题参考](../standards/topics.md)
- [TF 树](../standards/tf_tree.md)
