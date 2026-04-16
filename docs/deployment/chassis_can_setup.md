---
title: 底盘 CAN 部署
permalink: /chassis_can_setup
desc: Scout Mini 底盘的 CAN 适配器初始化、接口拉起与 ROS 2 启动方式。
breadcrumb: 部署与使用
layout: default
---

## 适用范围

本页主要针对：

- Scout Mini
- Scout Mini Omni
- 使用 CAN 接口连接底盘控制器
- 使用 `scout_ros2 + ugv_sdk` 驱动底盘

## 首次配置 CAN 适配器

`ugv_sdk` 已经提供了现成脚本：

```text
driver/ugv_sdk/scripts/setup_can2usb.bash
```

脚本实际执行的内容是：

```bash
sudo modprobe gs_usb
sudo ip link set can0 up type can bitrate 500000
sudo apt install -y can-utils
```

你可以直接运行：

```bash
bash ~/venom_ws/src/venom_vnv/driver/ugv_sdk/scripts/setup_can2usb.bash
```

## 后续每次重新插拔后的启动

如果 CAN 转 USB 设备已经初始化过，通常只需要重新拉起 `can0`：

```bash
bash ~/venom_ws/src/venom_vnv/driver/ugv_sdk/scripts/bringup_can2usb_500k.bash
```

这个脚本对应的命令是：

```bash
sudo ip link set can0 up type can bitrate 500000
```

## 检查 CAN 接口

确认 `can0` 是否存在：

```bash
ifconfig -a | grep can
```

也可以查看链路状态：

```bash
ip -details link show can0
```

## 调试建议

安装完 `can-utils` 后，可以用这些命令排查：

```bash
candump can0
```

如果总线正常，你应该能看到底盘相关 CAN 帧。

## 启动底盘 ROS 2 节点

一般 Scout Mini 建议直接启动对应 launch：

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch scout_base scout_mini_base.launch.py
```

如果是普通 Scout，可使用：

```bash
ros2 launch scout_base scout_base.launch.py
```

如果是 Scout Mini 全向底盘，可使用：

```bash
ros2 launch scout_base scout_mini_omni_base.launch.py
```

## 键盘遥控测试

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

## 常见问题

### 找不到 `can0`

- 检查 CAN 适配器是否已插入
- 重新执行 `sudo modprobe gs_usb`
- 再执行一次 `setup_can2usb.bash`

### `can0` 存在但底盘不响应

- 检查波特率是否为 `500000`
- 检查底盘是否处于可控状态
- 检查急停与遥控器模式
- 用 `candump can0` 看是否有帧收发

### 每次开机都要重新执行命令

如果你希望开机后自动配置 CAN 和路由，可以结合 [rc.local]({{ '/rc_local' | relative_url }}) 处理。

## 相关文档

- [底盘驱动]({{ '/chassis_driver' | relative_url }})
- [rc.local]({{ '/rc_local' | relative_url }})
