---
title: 底盘驱动总览
description: scout_ros2、hunter_ros2、ugv_sdk 的关系与统一接口约束。
---

# 底盘驱动总览

Venom VNV 当前的轮式底盘驱动链路主要由三部分组成：

- [Scout 底盘驱动](scout_ros2.md)
- [Hunter 底盘驱动](hunter_ros2.md)
- [UGV SDK](ugv_sdk.md)

其中：

- `scout_ros2` 负责 Scout / Scout Mini 系列的 ROS 2 封装
- `hunter_ros2` 负责 Hunter 系列的 ROS 2 封装
- `ugv_sdk` 负责 CAN 通信、协议解析和底层机器人接口抽象

## 模块关系

```text
用户应用 / bringup
        ↓ /cmd_vel
scout_ros2 或 hunter_ros2
        ↓ C++ 调用
      ugv_sdk
        ↓ CAN 帧
   CAN 适配器 / 车体控制器
```

## 支持硬件范围

- Scout 2.0
- Scout Mini
- Scout Mini Omni
- Hunter 1.0 / 2.0
- 以及 `ugv_sdk` 支持的更多 AgileX/Weston Robot 平台

## 统一接口约定

对于 Venom VNV 来说，底盘驱动层优先保证以下接口统一：

| 方向 | 话题 / TF | 说明 |
| --- | --- | --- |
| 订阅 | `/cmd_vel` | 接收上层速度控制指令 |
| 发布 | `/odom` | 发布底盘里程计 |
| 发布 | `odom -> base_link` | 广播底盘基础 TF |
| 发布 | 状态话题 | Scout 发布 `/scout_status`、`/rc_status`，Hunter 发布 `/hunter_status` |

如果后续整车接口要进一步标准化，优先在 `odom`、`base_link`、`/cmd_vel` 这一层保持兼容，不建议让上层直接耦合底层私有状态消息。

## 部署共性

无论是 Scout 还是 Hunter，部署时都要先把 CAN 链路打通。

### CAN 适配器配置

更完整的步骤可参考：[底盘 CAN 部署](../../deployment/chassis_can_setup.md)

```bash
sudo modprobe gs_usb
sudo ip link set can0 up type can bitrate 500000
ifconfig -a | grep can
```

`ugv_sdk/scripts/` 下提供了常用脚本：

- `setup_can2usb.bash`：首次配置 CAN-to-USB 适配器
- `bringup_can2usb.bash`：后续重插后快速拉起

### 基础验证

```bash
candump can0
```

如果连 `candump` 都收不到数据，先不要继续调 `scout_ros2` 或 `hunter_ros2`。

## 阅读顺序建议

1. 先看 [底盘 CAN 部署](../../deployment/chassis_can_setup.md) 完成物理链路与网卡配置
2. 再根据底盘型号阅读 [Scout 底盘驱动](scout_ros2.md) 或 [Hunter 底盘驱动](hunter_ros2.md)
3. 需要看底层协议与通信抽象时，再看 [UGV SDK](ugv_sdk.md)

## 故障排查

1. **CAN 通信不通**：先用 `candump can0` 看总线是否有数据
2. **底盘不动**：检查遥控器模式、急停、供电状态
3. **参数不一致**：检查 `port_name`、`odom_frame`、`base_frame`、`odom_topic_name`
4. **状态话题正常但运动异常**：继续往 `ugv_sdk` 和车体协议层排查

## 详细文档

- [Scout 底盘驱动](scout_ros2.md)
- [Hunter 底盘驱动](hunter_ros2.md)
- [UGV SDK](ugv_sdk.md)
