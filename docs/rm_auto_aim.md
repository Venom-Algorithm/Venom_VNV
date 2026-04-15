---
title: 自瞄算法总览
desc: rm_auto_aim — 装甲板检测、目标跟踪、弹道解算与统一控制输出。
breadcrumb: 自瞄算法
layout: default
---

## 模块定位

`rm_auto_aim` 是整套自瞄能力的算法集合，负责：

- 从相机图像中检测目标
- 对目标做连续跟踪和预测
- 进行弹道解算
- 输出最终云台控制与开火相关指令

它不是单个节点，而是一组协同工作的包。

## 子包结构

| 子包 | 功能 |
| --- | --- |
| `armor_detector` | 基于图像识别装甲板，并解算 3D 位置 |
| `armor_tracker` | 对装甲板观测做状态估计与目标管理 |
| `auto_aim_solver` | 将跟踪状态转换为 pitch/yaw 与开火控制量 |
| `auto_aim_interfaces` | 检测、跟踪、解算之间的统一消息定义 |

## 当前参数入口

这套链路里的参数分散在几个地方：

- 检测器参数：[armor_detector.yaml](/Users/liyh/venom_vnv/rm_auto_aim/armor_detector/config/armor_detector.yaml)
- 实战配置入口：[node_params.yaml](/Users/liyh/venom_vnv/venom_bringup/config/infantry/node_params.yaml)
- 弹道解算节点参数：[`solver_node.py`](/Users/liyh/venom_vnv/rm_auto_aim/auto_aim_solver/auto_aim_solver/solver_node.py)

## 数据流

```text
/image_raw
  -> armor_detector
  -> /detector/armors
  -> armor_tracker
  -> /tracker/target
  -> auto_aim_solver
  -> /auto_aim
  -> venom_serial_driver
  -> C-board
```

## 模块分工

1. `armor_detector`
负责“看见目标”。

2. `armor_tracker`
负责“持续理解同一个目标并预测其运动”。

3. `auto_aim_solver`
负责“把目标状态变成云台与射击控制量”。

4. `venom_serial_driver`
负责“把控制结果真正发给底层控制板”。

## `auto_aim_solver` 参数说明

`auto_aim_solver` 负责把检测/跟踪结果和枪口初速、TF 一起转换成最终控制量。当前代码中的参数如下：

| 参数名 | 作用 | 默认值 |
| --- | --- | --- |
| `mass` | 弹丸质量，单位 kg。 | `0.0032` |
| `radius` | 弹丸半径，单位 m。 | `0.0085` |
| `drag_coeff` | 阻力系数。 | `0.47` |
| `air_density` | 空气密度，单位 kg/m^3。 | `1.225` |
| `initial_speed` | 默认初速，单位 m/s。当未启用或未收到实时初速时使用。 | `28.0` |
| `launch_frame` | 枪口或发射器所在 TF。弹道解算会以它作为发射原点。 | `"launcher_link"` |
| `map_frame` | 目标状态所在的世界坐标系。 | `"odom"` |
| `command_frame` | 最终控制角度输出所参考的坐标系。留空时会退化为 `launch_frame`。 | `""` |
| `update_frequency` | 解算循环频率，单位 Hz。 | `30.0` |
| `target_topic` | 跟踪目标输入话题。 | `"/tracker/target"` |
| `target_timeout` | 跟踪目标超时阈值，单位秒。 | `0.2` |
| `speed_topic` | 实时初速输入话题。 | `"/game_status"` |
| `use_live_speed` | 是否优先使用底层回传的实时初速。 | `True` |
| `speed_timeout` | 实时初速超时阈值，单位秒。 | `0.5` |
| `min_live_speed` | 判定实时初速有效的最小值，单位 m/s。低于该值会回退到默认初速。 | `5.0` |
| `auto_fire` | 是否允许节点直接给出开火建议。 | `False` |
| `armor_topic` | 装甲板检测结果输入话题。部分模式下会直接用原始装甲板而非 tracker。 | `"/detector/armors"` |
| `armor_timeout` | 装甲板观测超时阈值，单位秒。 | `0.2` |
| `heat_reserve_ratio` | 预留热量比例。用于避免打满热量上限。 | `0.10` |
| `solver.min_pitch` | 弹道搜索 pitch 下界，单位 rad。 | `-0.35` |
| `solver.max_pitch` | 弹道搜索 pitch 上界，单位 rad。 | `0.8` |
| `solver.pitch_samples` | 初始 pitch 搜索采样数。值越大搜索更细，但耗时更高。 | `36` |
| `solver.max_iterations` | 单次弹道求解最大迭代次数。 | `18` |
| `solver.max_time` | 弹道积分或搜索的最大飞行时间，单位秒。 | `5.0` |
| `solver.ground_z` | 地面高度基准，单位米。 | `0.0` |
| `timing.pipeline_delay` | 感知链路固定延迟补偿，单位秒。 | `0.02` |
| `timing.control_delay` | 控制链路固定延迟补偿，单位秒。 | `0.015` |
| `auto_aim_topic` | 最终一体化控制消息输出话题。 | `"/auto_aim"` |
| `solution_topic` | 调试用云台角度解输出话题。 | `"/auto_aim/gimbal_cmd"` |
| `aim_point_topic` | 调试用瞄准点输出话题。 | `"/auto_aim/aim_point"` |
| `detect_topic` | 目标是否检测到的布尔量输出话题。 | `"/auto_aim/detect"` |
| `track_topic` | 目标是否正在跟踪的布尔量输出话题。 | `"/auto_aim/track"` |
| `fire_topic` | 是否建议开火的布尔量输出话题。 | `"/auto_aim/fire"` |
| `distance_topic` | 目标距离输出话题。 | `"/auto_aim/distance"` |
| `camera_info_topic` | 相机内参输入话题。 | `"/camera_info"` |
| `camera_frame` | 相机坐标系名称。用于几何恢复与投影。 | `"camera_link"` |

## 调参顺序

- 图像侧不稳，先调 [装甲板检测](armor_detector.md)
- 目标会跳、会丢，先调 [目标跟踪](armor_tracker.md)
- 检测和跟踪都正常但云台打不准，再调 `auto_aim_solver`
- 最终姿态方向不对或控制没下发，再查 [串口通信驱动](venom_serial_driver.md)

## 推荐启动方式

一般不建议单独逐个节点启动，更推荐由上层统一托管：

```bash
# 自瞄测试
ros2 launch venom_bringup autoaim_test_bringup.launch.py

# 导航 + 自瞄
ros2 launch venom_bringup autoaim_nav_bringup.launch.py
```

## 相关页面

- [装甲板检测](armor_detector.md)
- [目标跟踪](armor_tracker.md)
- [串口通信驱动](venom_serial_driver.md)
- [话题参考](topics.md)

## 进一步阅读

- [armor_detector README](../rm_auto_aim/armor_detector/README.md)
- [armor_tracker README](../rm_auto_aim/armor_tracker/README.md)
