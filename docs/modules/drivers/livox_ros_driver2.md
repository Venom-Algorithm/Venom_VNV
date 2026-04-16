---
title: Livox 雷达驱动
permalink: /livox_ros_driver2
desc: livox_ros_driver2 — Livox Mid360 激光雷达驱动。
breadcrumb: 硬件驱动
layout: default
---

## 模块定位

`livox_ros_driver2` 是 MID360 的官方驱动层，负责：

- 与雷达建立网络通信
- 接收并解析雷达原始数据
- 将数据发布为 ROS 2 可消费的话题
- 为 `Point-LIO`、`Fast-LIO` 等上层模块提供雷达输入

在系统中的数据流位置为：

`MID360 -> livox_ros_driver2 -> /livox/lidar + /livox/imu -> LIO`

## 输入与输出

| 方向 | 话题 | 消息类型 | 说明 |
| --- | --- | --- | --- |
| 发布 | `/livox/lidar` | `livox_ros_driver2/CustomMsg` 或 `sensor_msgs/PointCloud2` | 雷达点云输出 |
| 发布 | `/livox/imu` | `sensor_msgs/Imu` | 雷达内置 IMU 输出 |

## 依赖关系

这个包是以下模块的前置依赖：

- [Point-LIO]({{ '/point_lio' | relative_url }})
- [Fast-LIO]({{ '/fast_lio' | relative_url }})

如果驱动没有正常发布数据，上层 LIO 不会工作。

## 推荐启动方式

通常由雷达配置页中的流程启动：

```bash
ros2 launch livox_ros_driver2 msg_MID360_launch.py
```

## 配置文件

MID360 的关键配置通常集中在：

- `config/MID360_config.json`

推荐同时关注两层参数：

- launch 文件中的运行参数
- `config/MID360_config.json` 中的网络与设备参数

## 参数说明

### Launch 参数

| 参数名 | 作用 | 常用值 |
| --- | --- | --- |
| `xfer_format` | 输出点云格式选择。`0` 为 `PointCloud2`，`1` 为 Livox 自定义格式。 | `0` |
| `multi_topic` | 多雷达时是否一雷达一话题。单 MID360 通常保持关闭。 | `0` |
| `data_src` | 数据来源。当前正常在线雷达使用 `0`。 | `0` |
| `publish_freq` | 点云发布频率，单位 Hz。应与上层 LIO 预期频率匹配。 | `10.0` |
| `output_data_type` | 输出数据类型选择。通常按官方 MID360 launch 默认配置。 | `0` |
| `frame_id` | 输出点云与 IMU 的 frame id。若上层自行做外参和 TF 统一，这里通常保持雷达本体 frame。 | `"livox_frame"` |
| `user_config_path` | JSON 配置文件路径。指向实际使用的 MID360 网络配置文件。 | `config/MID360_config.json` |
| `cmdline_input_bd_code` | 指定设备广播码。单雷达场景下通常可不额外指定。 | 设备实际广播码 |

### `MID360_config.json` 参数

| 参数名 | 作用 | 说明 |
| --- | --- | --- |
| `lidar_summary_info.enable_connect` | 是否连接这台雷达。 | 单雷达部署必须为 `true`。 |
| `lidar_summary_info.lidar_type` | 设备类型。 | MID360 对应 `8`。 |
| `lidar_summary_info.host_net_info.host_ip` | 主机网卡 IP。 | 必须和雷达处于同一网段。 |
| `lidar_summary_info.host_net_info.cmd_data_port` | 主机命令数据端口。 | 用于控制通信。 |
| `lidar_summary_info.host_net_info.push_msg_port` | 主机状态消息端口。 | 用于接收状态与推送信息。 |
| `lidar_summary_info.host_net_info.point_data_port` | 主机点云数据端口。 | 用于接收点云数据。 |
| `lidar_summary_info.host_net_info.imu_data_port` | 主机 IMU 数据端口。 | 用于接收 IMU 数据。 |
| `lidar_summary_info.lidar_net_info.lidar_ip` | 雷达自身 IP。 | 必须与实际配置一致。 |
| `lidar_summary_info.lidar_net_info.cmd_data_port` | 雷达命令端口。 | 一般保持官方默认值。 |
| `lidar_summary_info.lidar_net_info.push_msg_port` | 雷达状态消息端口。 | 一般保持官方默认值。 |
| `lidar_summary_info.lidar_net_info.point_data_port` | 雷达点云发送端口。 | 一般保持官方默认值。 |
| `lidar_summary_info.lidar_net_info.imu_data_port` | 雷达 IMU 发送端口。 | 一般保持官方默认值。 |
| `lidar_configs.ip` | 当前配置对应的雷达 IP。 | 要和上面的 `lidar_ip` 对齐。 |
| `lidar_configs.pcl_data_type` | 点云数据类型。 | 会影响驱动最终输出数据形式。 |
| `lidar_configs.pattern_mode` | 回波/扫描模式。 | 通常按 MID360 官方推荐配置。 |
| `lidar_configs.extrinsic_parameter.roll/pitch/yaw` | 雷达外参角度。 | 如果上层 LIO 里已经固定外参，这里通常保持默认。 |
| `lidar_configs.extrinsic_parameter.x/y/z` | 雷达外参平移。 | 同上，一般不在驱动层重复做工程变换。 |

## 联调重点

- 先确保网卡静态 IP 正确
- 再确认雷达和主机之间链路可通
- 最后检查 `/livox/lidar` 与 `/livox/imu` 是否稳定发布

如果这里不通，不建议直接去调上层 LIO。

## 调参时最常见的判断逻辑

- 看不到设备：先检查 `host_ip`、`lidar_ip`、网卡静态 IP、网段是否一致
- 设备能连但没点云：再检查 `point_data_port`、`imu_data_port` 是否冲突
- 上层 LIO 时间错乱：检查 `publish_freq` 是否符合预期，以及上层是否假设了另一种时间戳单位或数据格式
- 非作者一键拉起时最容易出问题的地方，通常不是代码，而是 JSON 里的网络参数没改成当前机器环境

## 相关页面

- [配置雷达]({{ '/lidar_setup' | relative_url }})
- [Point-LIO]({{ '/point_lio' | relative_url }})
- [Fast-LIO]({{ '/fast_lio' | relative_url }})

## 进一步阅读

- [livox_ros_driver2 README](../driver/livox_ros_driver2/README.md)
