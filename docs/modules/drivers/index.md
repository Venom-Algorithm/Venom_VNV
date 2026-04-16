---
title: 驱动层
permalink: /driver_overview
desc: 各类硬件驱动包的职责、接口与依赖关系。
breadcrumb: 模块与接口
layout: default
---

## 模块划分

- [Livox 雷达驱动]({{ '/livox_ros_driver2' | relative_url }})
- [海康相机驱动]({{ '/ros2_hik_camera' | relative_url }})
- [底盘驱动]({{ '/chassis_driver' | relative_url }})
- [串口通信驱动]({{ '/venom_serial_driver' | relative_url }})

## 统一阅读视角

每个驱动文档建议统一回答这几个问题：

1. 它依赖什么硬件或 SDK
2. 它怎么启动
3. 它发布和订阅哪些 topic
4. 它在整机里扮演什么角色

## 系统位置

驱动层负责把现实设备接入 ROS 2 图谱，是所有上层算法的输入和输出边界。
