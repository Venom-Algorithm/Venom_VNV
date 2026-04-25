---
title: Piper 机械臂驱动
description: piper_ros — AgileX Piper 机械臂 ROS 2 控制、描述与仿真接口。
---

## 模块定位

`piper_ros` 是 Piper 机械臂的 ROS 2 接口集合，负责：

- 通过 CAN 控制机械臂本体
- 发布关节状态、末端位姿和机械臂状态
- 提供 URDF、MoveIt 和仿真相关包
- 为抓取或操作任务提供标准 ROS 2 接口

在系统中的链路位置为：

`控制命令 -> piper_ros -> CAN / piper_sdk -> Piper 机械臂`

## 仓库组成

当前仓库内可见的主要子包包括：

- `piper`：单臂控制节点
- `piper_msgs`：机械臂状态与控制消息
- `piper_description`：URDF 与显示相关内容
- `piper_moveit`：MoveIt 配置
- `piper_sim`：Gazebo 仿真
- `piper_humble`：Humble 适配相关内容

## 依赖关系

这个模块通常依赖：

- `python-can`
- `piper_sdk`
- `ros2_control`
- `ros2_controllers`
- `controller_manager`

同时它对 CAN 适配器也有明确要求，仓库说明中强调优先使用机械臂官方 CAN 模块。

## 输入与输出

单臂控制节点 `piper_single_ctrl` 的核心接口包括：

| 方向 | 话题 / 服务 | 类型 | 说明 |
| --- | --- | --- | --- |
| 订阅 | `joint_ctrl_single` | `sensor_msgs/JointState` | 关节控制输入 |
| 订阅 | `pos_cmd` | `piper_msgs/PosCmd` | 末端位姿控制输入 |
| 订阅 | `enable_flag` | `std_msgs/Bool` | 机械臂使能控制 |
| 发布 | `joint_states_single` | `sensor_msgs/JointState` | 当前关节状态 |
| 发布 | `joint_states_feedback` | `sensor_msgs/JointState` | 反馈关节状态 |
| 发布 | `joint_ctrl` | `sensor_msgs/JointState` | 当前控制目标反馈 |
| 发布 | `arm_status` | `piper_msgs/PiperStatusMsg` | 机械臂整体状态 |
| 发布 | `end_pose` | `geometry_msgs/Pose` | 末端位姿 |
| 发布 | `end_pose_stamped` | `geometry_msgs/PoseStamped` | 带时间戳的末端位姿 |
| 服务 | `enable_srv` | `piper_msgs/srv/Enable` | 机械臂使能服务 |

## 推荐启动方式

单臂控制常用启动方式：

```bash
ros2 launch piper start_single_piper.launch.py
```

如果希望同时带 RViz 调试，可使用：

```bash
ros2 launch piper start_single_piper_rviz.launch.py
```

## 核心参数

`piper_single_ctrl` 中常见参数包括：

| 参数名 | 作用 | 常用值 |
| --- | --- | --- |
| `can_port` | 使用的 CAN 接口名称 | `can0` |
| `auto_enable` | 启动后是否自动使能机械臂 | `false` |
| `gripper_exist` | 是否带夹爪 | `true` / `false` |
| `gripper_val_mutiple` | 夹爪控制倍率 | `1` 或 `2` |

## 部署注意事项

- Piper 默认 CAN 波特率与底盘不同，常见为 `1000000`
- 如果同一台机器同时接机械臂和底盘，建议给 CAN 接口使用明确命名
- 官方仓库强调不同固件版本对应的 URDF 可能不同，部署前要确认机械臂固件版本
- 如果只做显示、MoveIt 或仿真，还要结合 `piper_description`、`piper_moveit`、`piper_sim` 一起使用

## 相关页面

- [驱动层总览](index.md)
- [机械臂 CAN 部署](../../deployment/piper_can_setup.md)
- [系统启动](../integration/venom_bringup.md)
- [话题参考](../standards/topics.md)

## 进一步阅读

- [piper_ros README](https://github.com/Venom-Algorithm/Venom_VNV/blob/master/driver/piper_ros/README.MD)
