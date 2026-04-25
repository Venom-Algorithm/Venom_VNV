---
title: UGV SDK
description: ugv_sdk — AgileX / Weston Robot 轮式底盘底层 C++ SDK。
---

## 模块定位

`ugv_sdk` 不是直接给整车使用的 ROS 2 节点，而是 Scout、Hunter 等底盘驱动的底层通信库。

它主要负责：

- 与底盘控制器进行 CAN 通信
- 把原始 CAN 帧翻译为 C++ 结构体与控制接口
- 为不同底盘型号提供统一抽象
- 提供 CAN 配置脚本和样例程序

在系统中的位置为：

`scout_ros2 / hunter_ros2 -> ugv_sdk -> CAN -> 底盘控制器`

## 支持范围

根据当前仓库内说明，`ugv_sdk` 支持包括但不限于：

- Scout / Scout Mini / Scout Mini Omni
- Hunter 1.0 / 2.0
- Bunker
- Tracer
- Ranger 系列

Venom VNV 当前重点使用的是 Scout 和 Hunter 两条链路。

## 代码层抽象

`ugv_sdk` 内部大致分为三层：

1. `interface`：定义机器人公共接口
2. `robot_base`：实现各型号与协议版本
3. `mobile_robot`：在运行时选择具体机器人类型

如果你只是整车部署，一般只需要知道它存在并且被上层驱动调用；如果你要改底层通信或协议适配，就需要进入这一层。

## 常用脚本与工具

`ugv_sdk/scripts/` 下常用脚本包括：

- `setup_can2usb.bash`：首次配置 CAN-to-USB
- `bringup_can2usb.bash`：重插后的快速恢复

基础调试命令：

```bash
sudo modprobe gs_usb
sudo ip link set can0 up type can bitrate 500000
candump can0
```

## 与 ROS 驱动的关系

`ugv_sdk` 本身不直接定义标准 ROS 2 话题接口。对整车来说：

- `scout_ros2` 负责把它封装成 `/cmd_vel`、`/odom`、`/scout_status`
- `hunter_ros2` 负责把它封装成 `/cmd_vel`、`/odom`、`/hunter_status`

如果 CAN 总线没通，或者 SDK 层通信异常，上面的 ROS 2 驱动也会一起失效。

## 调试建议

- 先检查物理链路与 CAN 设备
- 再检查 `candump` 是否能收到数据
- 再运行 `scout_ros2` / `hunter_ros2`
- 如果需要更细粒度验证，可参考 `sample/` 目录下的 demo

## 相关页面

- [底盘驱动总览](chassis_driver.md)
- [Scout 底盘驱动](scout_ros2.md)
- [Hunter 底盘驱动](hunter_ros2.md)

## 进一步阅读

- [ugv_sdk README](https://github.com/Venom-Algorithm/Venom_VNV/blob/master/driver/ugv_sdk/README.md)
- [ugv_sdk docs](https://github.com/Venom-Algorithm/Venom_VNV/tree/master/driver/ugv_sdk/docs)
