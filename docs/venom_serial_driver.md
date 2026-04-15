---
title: 串口通信驱动
desc: venom_serial_driver — NUC 与 DJI C 板串口通信驱动。
breadcrumb: 硬件驱动
layout: default
---

## 模块定位

`venom_serial_driver` 是 NUC 与 DJI C 板之间的串口桥接层，负责：

- 接收上层 `/cmd_vel` 与 `/auto_aim`
- 打包成下位机协议帧并通过串口发送
- 解析 C 板回传状态
- 向 ROS 2 发布底盘状态、比赛状态和枪口初速等信息

它是导航控制、自瞄控制与底层执行机构之间的统一出口。

## 输入与输出

完整系统级话题参考见 [topics.md](./topics.md)。

### 订阅

| 话题 | 消息类型 | 说明 |
|---|---|---|
| `/cmd_vel` | `geometry_msgs/Twist` | 底盘速度指令。当前驱动实际使用 `linear.x`、`linear.y` 和 `angular.z`。 |
| `/auto_aim` | `venom_serial_driver/AutoAimCmd` | 自瞄控制量，包括 pitch、yaw、检测状态、跟踪状态、开火标志、距离和图像投影点。 |

### 发布

| 话题 | 消息类型 | 说明 |
|---|---|---|
| `/robot_status` | `venom_serial_driver/RobotStatus` | C 板回传的机器人状态，包括底盘速度与云台角度等。 |
| `/game_status` | `venom_serial_driver/GameStatus` | 比赛状态，包括血量、枪口热量、比赛进程、RFID 等。 |

## 推荐启动方式

```bash
ros2 launch venom_serial_driver serial_driver.launch.py
```

## 参数说明

当前默认配置文件：

- [serial_params.yaml](/Users/liyh/venom_vnv/driver/venom_serial_driver/config/serial_params.yaml)

| 参数名 | 作用 | 默认值 |
| --- | --- | --- |
| `port_name` | 串口设备路径。必须和实际 USB 转串口设备一致。 | `"/dev/ttyUSB0"` |
| `baud_rate` | 串口波特率。要与 C 板协议设置完全一致。 | `921600` |
| `timeout` | 串口读超时，单位秒。过小会频繁空读，过大则影响异常恢复速度。 | `0.1` |
| `loop_rate` | 串口接收轮询频率，单位 Hz。值越大，状态更新越及时，但 CPU 占用更高。 | `50` |
| `cmd_vel_topic` | 底盘速度命令输入话题。 | `"/cmd_vel"` |
| `auto_aim_topic` | 自瞄控制输入话题。 | `"/auto_aim"` |
| `venom_cmd_topic` | 文本调试/状态汇总输出话题。 | `"/venom_cmd"` |
| `robot_status_topic` | 机器人状态输出话题。 | `"/robot_status"` |
| `game_status_topic` | 比赛状态输出话题。 | `"/game_status"` |
| `vision_timeout` | 自瞄指令超时阈值，单位秒。超过后串口节点会把旧的视觉控制视为过期。 | `0.2` |
| `default_frame_x` | 当视觉没有给出图像坐标时使用的默认像素 x。 | `0` |
| `default_frame_y` | 当视觉没有给出图像坐标时使用的默认像素 y。 | `0` |
| `pitch_sign` | pitch 方向符号修正。云台方向与软件约定不一致时可用它翻转。 | `1.0` |
| `yaw_sign` | yaw 方向符号修正。云台方向与软件约定不一致时可用它翻转。 | `1.0` |
| `heartbeat_rate` | 最小控制发送频率，单位 Hz。`0.0` 表示关闭心跳，仅在收到新命令时发送。 | `0.0` |

## 调试重点

- 串口打不开，先查 `port_name` 和设备权限
- 控制有延迟，先查 `loop_rate`、`heartbeat_rate` 和底层串口缓存
- 云台左右或上下反了，优先改 `pitch_sign` / `yaw_sign`
- 自瞄偶尔掉控制，优先查 `vision_timeout` 是否过短

## 通信协议

完整二进制协议说明见 [protocol.md](protocol.md)。

### 帧格式

**NUC -> C 板（控制指令）**
```
[0xA5][len(2)][0x02][data][CRC16(2)]
```

**C 板 -> NUC（状态回传）**
```
[0x5A][len(2)][0x01][data][CRC16(2)]
```

## 测试方法

### 查看状态回传

```bash
ros2 topic echo /robot_status
ros2 topic echo /game_status
```

### 发送底盘速度指令

```bash
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 0.1, y: 0.0, z: 0.0}}'
```

### 发送自瞄控制指令

```bash
ros2 topic pub /auto_aim venom_serial_driver/msg/AutoAimCmd \
  '{pitch: 0.1, yaw: 0.2, detected: true, tracking: true, fire: false, distance: 3.0, proj_x: 640, proj_y: 360}'
```

### 硬件联调脚本

下面这些脚本需要真实串口硬件连接：

```bash
# 回环与 CRC 校验
python3 test/test_loopback.py /dev/ttyUSB0

# 实时状态监视（不依赖 ROS 完整环境）
python3 test/test_monitor.py --port /dev/ttyUSB0

# 云台 yaw 旋转测试
python3 test/test_hardware.py --port /dev/ttyUSB0 --test yaw

# 底盘运动测试
python3 test/test_hardware.py --port /dev/ttyUSB0 --test chassis
```

## 常见问题

1. **串口权限不足**
   ```bash
   sudo chmod 666 /dev/ttyUSB0
   ```

2. **检查串口设备路径**
   ```bash
   ls /dev/ttyUSB*
   ```

3. **开启调试日志**
   ```bash
   ros2 run venom_serial_driver serial_node --ros-args --log-level debug
   ```
