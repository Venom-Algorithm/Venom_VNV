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
