# ros2_hik_camera

海康 USB3.0 工业相机 ROS2 驱动，用于自瞄系统的图像采集。

## 功能

- 海康 MVS SDK 内嵌，无需系统级驱动安装
- 支持 amd64（x86_64）和 arm64（Jetson Orin 等）
- 通过 YAML 配置曝光、增益和相机内参
- 发布标准 ROS2 图像话题

## 快速开始

```bash
ros2 launch hik_camera hik_camera.launch.py
```

## ROS 2 话题

| 方向 | 话题 | 消息类型 | 说明 |
|------|------|----------|------|
| 发布 | `/image_raw` | `sensor_msgs/Image` | 原始图像流 |
| 发布 | `/camera_info` | `sensor_msgs/CameraInfo` | 相机内参 |

## 参数配置

编辑 `config/camera_params.yaml`：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `exposure_time` | float | 5000.0 | 曝光时间（微秒） |
| `gain` | float | 16.0 | 模拟增益 |

相机内参标定数据在 `config/camera_info.yaml` 中配置。

## 多平台支持

SDK 已内嵌在 `hikSDK/` 目录中：
- `hikSDK/lib/amd64/` — x86_64 平台
- `hikSDK/lib/arm64/` — ARM64 平台（Jetson Orin/Xavier）

## 详细文档

详见：[ros2_hik_camera README](../driver/ros2_hik_camera/README.md)
