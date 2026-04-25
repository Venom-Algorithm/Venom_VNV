---
title: 海康相机驱动
description: ros2_hik_camera — 海康 USB3.0 工业相机 ROS2 驱动。
---

## 模块定位

`ros2_hik_camera` 是自瞄链路的图像输入驱动，负责：

- 初始化海康工业相机
- 采集原始图像
- 发布标准 ROS 2 图像与相机内参话题
- 为 `armor_detector` 提供稳定图像源

在系统中的数据流位置为：

`Hik Camera -> ros2_hik_camera -> /image_raw + /camera_info -> armor_detector`

## 输入与输出

| 方向 | 话题 | 消息类型 | 说明 |
| --- | --- | --- | --- |
| 发布 | `/image_raw` | `sensor_msgs/Image` | 原始图像流 |
| 发布 | `/camera_info` | `sensor_msgs/CameraInfo` | 相机内参、畸变与标定结果 |

## 配置文件

常见配置文件包括：

- `config/camera_params.yaml`
- `config/camera_info.yaml`

前者主要控制运行参数：

- 曝光时间
- 增益
- 帧率或触发模式

后者主要存放标定结果：

- 相机矩阵
- 畸变参数
- 图像分辨率

## 参数说明

### `camera_params.yaml`

| 参数名 | 作用 | 默认值 |
| --- | --- | --- |
| `camera_name` | 相机标定名称，供 `camera_info_manager` 读取与匹配相机信息。 | `"narrow_stereo"` |
| `exposure_time` | 曝光时间，单位微秒。值越大图像越亮，但运动拖影会更明显。 | `6000` |
| `gain` | 模拟/数字增益。值越大图像越亮，但噪声也会更明显。 | `10.0` |
| `frame_id` | 图像与相机内参消息使用的坐标系名称。 | `"camera_link"` |
| `camera_info_url` | 标定文件路径。驱动会从这里读取内参与畸变参数。 | `"package://venom_bringup/config/camera_info.yaml"` |
| `use_sensor_data_qos` | 是否使用 `SensorDataQoS` 发布图像。开启后延迟更低，但在弱网络或桥接场景下更容易丢帧。 | `false` |

### `camera_info.yaml`

`camera_info.yaml` 里不是算法调参，而是标定结果。最关键的是：

- `image_width` / `image_height`：标定对应的分辨率
- `camera_matrix`：相机内参矩阵，决定 PnP 解算尺度
- `distortion_coefficients`：畸变参数
- `rectification_matrix` / `projection_matrix`：后续图像处理和几何投影使用

这里如果填错，`armor_detector` 即使 2D 检测正常，3D 解算也会明显偏。

## 推荐启动方式

单独调试时：

```bash
ros2 launch hik_camera hik_camera.launch.py
```

完整自瞄链路中更推荐由 `venom_bringup` 统一启动。

## 调试重点

- 先检查相机是否枚举成功
- 再检查 `/image_raw` 是否连续稳定
- 最后检查 `/camera_info` 是否与当前镜头标定一致

常见调参逻辑：

- 画面偏暗，先加 `exposure_time`，再看是否必须加 `gain`
- 目标拖影明显，优先降低 `exposure_time`，不要只靠后处理补救
- 图像正常但位姿偏，先查 `camera_info_url` 指向的标定文件

如果图像正常但检测 3D 位置异常，通常不是驱动本身的问题，而是 `camera_info` 或装甲板尺寸配置的问题。

## 相关页面

- [自瞄算法总览](../auto_aim/index.md)
- [装甲板检测](../auto_aim/armor_detector.md)
- [话题参考](../standards/topics.md)

## 进一步阅读

- [ros2_hik_camera README](https://github.com/Venom-Algorithm/Venom_VNV/blob/master/driver/ros2_hik_camera/README.md)
