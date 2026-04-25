---
title: Scout 底盘驱动
description: scout_ros2 — AgileX Scout / Scout Mini 系列底盘 ROS 2 驱动。
---

## 模块定位

`scout_ros2` 是 Scout 系列底盘的 ROS 2 封装层，负责：

- 接收 ROS 2 层的速度控制命令
- 调用 `ugv_sdk` 与底盘控制器通信
- 发布底盘里程计、状态和遥控器状态
- 向上层提供标准 `/cmd_vel`、`/odom`、TF 接口

在系统中的链路位置为：

`/cmd_vel -> scout_ros2 -> ugv_sdk -> CAN -> Scout 底盘`

## 仓库组成

`scout_ros2` 主要包含：

- `scout_base`：底盘控制与状态发布主节点
- `scout_description`：URDF 与描述文件
- `scout_msgs`：状态与灯光等消息定义

## 输入与输出

| 方向 | 话题 / TF | 消息类型 | 说明 |
| --- | --- | --- | --- |
| 订阅 | `/cmd_vel` | `geometry_msgs/Twist` | 底盘速度控制命令 |
| 订阅 | `/light_control` | `scout_msgs/ScoutLightCmd` | 灯光控制命令 |
| 发布 | `/odom` | `nav_msgs/Odometry` | 底盘里程计输出 |
| 发布 | `/scout_status` | `scout_msgs/ScoutStatus` | 整车状态反馈 |
| 发布 | `/rc_status` | `scout_msgs/ScoutRCState` | 遥控器状态反馈 |
| 发布 | `odom -> base_link` | `tf2` | 底盘基础 TF |

## 依赖关系

这个包依赖：

- [UGV SDK](ugv_sdk.md)
- CAN 适配器与底盘通信链路

如果底层 CAN 或 `ugv_sdk` 没通，`scout_ros2` 不会正常输出里程计和状态。

## 推荐启动方式

根据具体车型选择 launch：

```bash
ros2 launch scout_base scout_base.launch.py
```

如果使用 Scout Mini 或全向版本，可使用：

```bash
ros2 launch scout_base scout_mini_base.launch.py
ros2 launch scout_base scout_mini_omni_base.launch.py
```

## 核心参数

`scout_base` 中常见参数包括：

| 参数名 | 作用 | 常用值 |
| --- | --- | --- |
| `port_name` | CAN 设备名称 | `can0` |
| `odom_frame` | 里程计坐标系名称 | `odom` |
| `base_frame` | 车体坐标系名称 | `base_link` |
| `odom_topic_name` | 里程计话题名 | `odom` |
| `is_scout_mini` | 是否使用 Scout Mini 模型 | `false` / `true` |
| `is_omni_wheel` | 是否为全向轮版本 | `false` / `true` |
| `simulated_robot` | 是否仿真模式 | `false` |
| `control_rate` | 控制循环频率 | `50` |

## 联调重点

- 先确认 `can0` 是否已正常拉起
- 再确认 `/scout_status` 与 `/odom` 是否稳定发布
- 再检查 `odom -> base_link` 是否和整车 TF 约定一致
- 如果整车只要求标准接口，上层优先依赖 `/cmd_vel`、`/odom` 和 TF，不要直接绑死私有状态话题

## 相关页面

- [底盘驱动总览](chassis_driver.md)
- [UGV SDK](ugv_sdk.md)
- [底盘 CAN 部署](../../deployment/chassis_can_setup.md)

## 进一步阅读

- [scout_ros2 README](https://github.com/Venom-Algorithm/Venom_VNV/blob/master/driver/scout_ros2/README.md)
