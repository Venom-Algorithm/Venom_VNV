---
title: 故障排查
description: 按子系统分类的排障入口与建议检查顺序。
---

## 雷达

- 网卡静态 IP 是否正确
- 配置文件中的主机地址是否匹配
- 驱动是否正常发布 `/livox/lidar`

## 相机

- 相机是否被系统识别
- SDK 是否可用
- `/image_raw` 和 `/camera_info` 是否正常发布

## 底盘与 CAN

- `can0` 是否成功建立
- 底盘协议版本是否匹配

## 串口

- 串口设备名、波特率、权限是否正确
- `/robot_status` 和 `/game_status` 是否有输出

## 定位与自瞄

- TF 链是否完整
- 上游输入 topic 是否存在
- bringup 启动模式是否正确

## Point-LIO

- 初始化阶段看到 `Keep the LiDAR-IMU device stationary` 时，雷达和 IMU 必须保持静止，直到出现 `initial local map is ready`
- 看到 `dropped old LiDAR frame(s)` 或 `dropped old IMU sample(s)`，先检查 CPU 负载、DDS 是否堵塞、点云 / IMU 发布频率是否异常
- 看到 `dropped old map job(s)`，说明异步地图线程跟不上，可增大地图发布间隔、调稀 `/map_cloud` 或暂时关闭地图发布
- 看到 `odometry loop overrun`，说明里程计主循环已经超过 LiDAR 帧间隔，优先降低当前帧点数和可视化发布负载
- 看到 `sync warning`，先检查 `/livox/lidar` 与 `/livox/imu` 时间戳和录包完整性，不要第一时间改匹配参数
