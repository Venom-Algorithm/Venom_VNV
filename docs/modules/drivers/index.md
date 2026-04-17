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
- [底盘驱动总览]({{ '/chassis_driver' | relative_url }})
- [Scout 底盘驱动]({{ '/scout_ros2' | relative_url }})
- [Hunter 底盘驱动]({{ '/hunter_ros2' | relative_url }})
- [UGV SDK]({{ '/ugv_sdk' | relative_url }})
- [Piper 机械臂驱动]({{ '/piper_ros' | relative_url }})
- [PX4 Bridge]({{ '/venom_px4_bridge' | relative_url }})
- [串口通信驱动]({{ '/venom_serial_driver' | relative_url }})

## 当前覆盖的驱动子项目

| 分类 | 子项目 | 文档入口 | 说明 |
| --- | --- | --- | --- |
| 雷达 | `livox_ros_driver2` | [Livox 雷达驱动]({{ '/livox_ros_driver2' | relative_url }}) | Mid360 点云与 IMU 输入 |
| 相机 | `ros2_hik_camera` | [海康相机驱动]({{ '/ros2_hik_camera' | relative_url }}) | 图像与相机内参输入 |
| 底盘 | `scout_ros2` | [Scout 底盘驱动]({{ '/scout_ros2' | relative_url }}) | Scout 系列底盘 ROS 2 封装 |
| 底盘 | `hunter_ros2` | [Hunter 底盘驱动]({{ '/hunter_ros2' | relative_url }}) | Hunter 系列底盘 ROS 2 封装 |
| 底盘 | `ugv_sdk` | [UGV SDK]({{ '/ugv_sdk' | relative_url }}) | 底层 C++ SDK、CAN 抽象与工具脚本 |
| 机械臂 | `piper_ros` | [Piper 机械臂驱动]({{ '/piper_ros' | relative_url }}) | 机械臂控制、URDF、MoveIt 与仿真 |
| 飞控桥接 | `venom_px4_bridge` | [PX4 Bridge]({{ '/venom_px4_bridge' | relative_url }}) | PX4 ROS 2 消息、DDS 探测与桥接状态输出 |
| 串口 | `venom_serial_driver` | [串口通信驱动]({{ '/venom_serial_driver' | relative_url }}) | 上下位机通信 |

## 统一阅读视角

每个驱动文档建议统一回答这几个问题：

1. 它依赖什么硬件或 SDK
2. 它怎么启动
3. 它发布和订阅哪些 topic
4. 它在整机里扮演什么角色

## 系统位置

驱动层负责把现实设备接入 ROS 2 图谱，是所有上层算法的输入和输出边界。
