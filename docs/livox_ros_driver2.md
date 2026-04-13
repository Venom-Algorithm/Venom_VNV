# livox_ros_driver2

Livox 第二代激光雷达驱动，本项目使用 Mid360 型号。

## 功能

- 支持 Livox HAP / Mid360 激光雷达
- 兼容 ROS1 和 ROS2
- 支持 PointCloud2 和 Livox 自定义点云格式
- JSON 配置 LiDAR 参数（IP、端口、数据类型等）

## 与系统集成

本项目中 livox_ros_driver2 是 Point-LIO 的前置依赖，数据流：

```
Livox Mid360 → livox_ros_driver2 → /livox/lidar → Point-LIO
```

## 启动

```bash
# 通过 venom_bringup 统一启动（推荐）
ros2 launch venom_bringup mapping_bringup.launch.py

# 单独启动 Mid360 驱动
ros2 launch livox_ros_driver2 msg_MID360_launch.py
```

## 配置要点

1. 先安装 [Livox-SDK2](https://github.com/Livox-SDK/Livox-SDK2)
2. 配置有线网卡静态 IP（`192.168.1.50`）
3. 修改 `config/MID360_config.json` 中的 host IP 和 LiDAR IP
4. Mid360 默认 IP 为 `192.168.1.1xx`（xx 为序列号后两位）

详细装配步骤见 [setup.md](setup.md)

## 详细文档

详见：[livox_ros_driver2 README](../driver/livox_ros_driver2/README.md)
