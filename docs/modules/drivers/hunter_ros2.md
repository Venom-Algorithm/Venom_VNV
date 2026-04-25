---
title: Hunter 底盘驱动
description: hunter_ros2 — AgileX Hunter 系列底盘 ROS 2 驱动。
---

## 模块定位

`hunter_ros2` 是 Hunter 系列底盘的 ROS 2 封装层，负责：

- 接收上层发送的 `/cmd_vel`
- 通过 `ugv_sdk` 与 Hunter 底盘通信
- 发布底盘里程计与 Hunter 专用状态话题
- 向整车系统暴露标准 `odom -> base_link` TF

在系统中的链路位置为：

`/cmd_vel -> hunter_ros2 -> ugv_sdk -> CAN -> Hunter 底盘`

## 仓库组成

`hunter_ros2` 主要包含：

- `hunter_base`：Hunter 底盘主控制节点
- `hunter_msgs`：Hunter 状态消息定义

## 输入与输出

| 方向 | 话题 / TF | 消息类型 | 说明 |
| --- | --- | --- | --- |
| 订阅 | `/cmd_vel` | `geometry_msgs/Twist` | 底盘速度控制命令 |
| 发布 | `/odom` | `nav_msgs/Odometry` | 底盘里程计 |
| 发布 | `/hunter_status` | `hunter_msgs/HunterStatus` | 车体状态反馈 |
| 发布 | `odom -> base_link` | `tf2` | 底盘基础 TF |

## 依赖关系

这个包依赖：

- [UGV SDK](ugv_sdk.md)
- CAN 总线通信链路

Hunter 是转向式底盘，虽然对上层仍然暴露 `/cmd_vel`，但内部运动学与 Scout 的差异较大，因此建议把它当成独立驱动模块理解和调试。

## 推荐启动方式

```bash
ros2 launch hunter_base hunter_base.launch.py
```

## 核心参数

`hunter_base` 中常见参数包括：

| 参数名 | 作用 | 常用值 |
| --- | --- | --- |
| `port_name` | CAN 设备名称 | `can0` |
| `odom_frame` | 里程计坐标系名称 | `odom` |
| `base_frame` | 车体坐标系名称 | `base_link` |
| `odom_topic_name` | 里程计话题名 | `odom` |
| `is_hunter_mini` | 是否使用特定 Hunter 变体参数 | `false` |
| `simulated_robot` | 是否仿真模式 | `false` |
| `control_rate` | 控制循环频率 | `50` |

## 联调重点

- 先用 `candump can0` 确认 CAN 正常
- 再检查 `/hunter_status` 和 `/odom` 是否同步发布
- 再确认 `odom` 与 `base_link` 是否满足整车 TF 约定
- Hunter 的角速度由转向角间接决定，若运动学表现异常，应继续往底层状态和底盘参数排查

## 相关页面

- [底盘驱动总览](chassis_driver.md)
- [UGV SDK](ugv_sdk.md)
- [底盘 CAN 部署](../../deployment/chassis_can_setup.md)

## 进一步阅读

- [hunter_ros2 README](https://github.com/Venom-Algorithm/Venom_VNV/blob/master/driver/hunter_ros2/README.md)
