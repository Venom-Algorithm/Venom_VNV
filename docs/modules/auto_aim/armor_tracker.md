---
title: 目标跟踪
permalink: /armor_tracker
desc: armor_tracker — EKF 多目标跟踪，运动预测与补偿。
breadcrumb: 自瞄算法
layout: default
---

## 模块定位

`armor_tracker` 是自瞄链路中的状态估计模块，负责：

- 接收 `armor_detector` 输出的装甲板观测
- 进行目标关联、状态估计与预测
- 向后级弹道解算或控制器输出更稳定的目标状态

在整套链路中的位置为：

`/detector/armors -> armor_tracker -> /tracker/target`

## 输入与输出

| 方向 | 话题 | 消息类型 | 说明 |
| --- | --- | --- | --- |
| 订阅 | `/detector/armors` | `auto_aim_interfaces/Armors` | 检测器输出的装甲板观测 |
| 发布 | `/tracker/target` | `auto_aim_interfaces/Target` | 当前被跟踪目标的状态估计结果 |
| 发布 | `/tracker/info` | `auto_aim_interfaces/TrackerInfo` | 跟踪调试信息，如残差、跟踪状态等 |

## 核心职责

- 目标关联：决定当前观测属于哪个目标
- EKF 估计：估计目标位置、速度、朝向等状态
- 短时预测：在观测稀疏或目标高速运动时提供前向预测
- 目标管理：处理新目标建立、目标切换、目标丢失与重捕获

## 参数说明

当前实战配置入口：

- [infantry/node_params.yaml](/Users/liyh/venom_vnv/venom_bringup/config/infantry/node_params.yaml)

源码中的完整参数入口在：

- [`tracker_node.cpp`](/Users/liyh/venom_vnv/perception/rm_auto_aim/armor_tracker/src/tracker_node.cpp)

下面表格中的“默认值”指源码默认值。实战启动时如果 `node_params.yaml` 里做了覆盖，应以 bringup 传入的值为准。

| 参数名 | 作用 | 默认值 |
| --- | --- | --- |
| `max_armor_distance` | 允许参与跟踪的最大平面距离，单位米。超出后会被视为异常观测。 | `10.0` |
| `min_armor_z` | 允许参与跟踪的最小高度，单位米。 | `-1.2` |
| `max_armor_z` | 允许参与跟踪的最大高度，单位米。 | `1.2` |
| `tracker.max_match_distance` | 观测与当前目标匹配的最大距离门限，单位米。越小越严格。 | `0.15` |
| `tracker.max_match_yaw_diff` | 观测与当前目标匹配的最大 yaw 差门限，单位 rad。 | `1.0` |
| `tracker.tracking_thres` | 从临时状态转为稳定跟踪所需的连续命中次数。 | `5` |
| `tracker.lost_time_thres` | 连续丢失多久后判定目标彻底丢失，单位秒。 | `0.3` |
| `ekf.sigma2_q_xyz` | EKF 位置过程噪声。值越大，滤波器越允许目标平移状态快速变化。 | `20.0` |
| `ekf.sigma2_q_yaw` | EKF yaw 过程噪声。值越大，滤波器越允许目标转动更剧烈。 | `100.0` |
| `ekf.sigma2_q_r` | EKF 装甲半径/结构参数过程噪声。 | `800.0` |
| `ekf.r_xyz_factor` | 位置观测噪声因子。距离越远，测量噪声会按该因子放大。 | `0.05` |
| `ekf.r_yaw` | yaw 观测噪声。 | `0.02` |
| `target_frame` | 跟踪器内部统一使用的目标坐标系。所有装甲板观测会先变换到这里。 | `"odom"` |

## 推荐启动方式

通常不单独启动，建议由上层统一托管：

```bash
# 步兵自瞄链路（推荐）
ros2 launch venom_bringup infantry_auto_aim.launch.py
```

如需单独调试：

```bash
ros2 run armor_tracker armor_tracker_node
```

## 调试重点

- 若 `/tracker/target` 不稳定，先确认 `/detector/armors` 观测是否连续
- 若目标频繁丢失或切换，优先检查关联逻辑与阈值，而不是先改弹道部分
- 若跟踪存在明显延迟，应联合检查相机频率、检测频率与 EKF 参数

常见调参逻辑：

- 目标老是串目标，先收紧 `tracker.max_match_distance` 和 `tracker.max_match_yaw_diff`
- 目标容易刚出现就丢，先放宽 `tracker.tracking_thres` / `tracker.lost_time_thres`
- 预测太“硬”，就适当增大 `ekf.sigma2_q_xyz`、`ekf.sigma2_q_yaw`
- 轨迹抖动太大，再考虑调大 `ekf.r_xyz_factor` 或 `ekf.r_yaw`

## 相关页面

- [自瞄算法总览]({{ '/rm_auto_aim' | relative_url }})
- [装甲板检测]({{ '/armor_detector' | relative_url }})
- [话题参考]({{ '/topics' | relative_url }})

## 进一步阅读

- [armor_tracker README](../../../perception/rm_auto_aim/armor_tracker/README.md)
