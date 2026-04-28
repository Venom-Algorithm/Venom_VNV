---
title: TEB Controller
description: venom_teb_controller - Nav2 controller 插件形式的 TEB 局部规划器。
---

## 模块定位

`planning/navigation/venom_teb_controller` 是当前接入的二维局部轨迹优化与 controller 子模块。

它的核心包不是一个独立整机启动入口，而是 Nav2 `controller_server` 可加载的 controller 插件：

| 内容 | 当前值 |
| --- | --- |
| 子模块路径 | `planning/navigation/venom_teb_controller` |
| controller 包名 | `teb_local_planner` |
| 消息包名 | `teb_msgs` |
| 插件类型 | `teb_local_planner::TebLocalPlannerROS` |
| pluginlib 声明 | `planning/navigation/venom_teb_controller/venom_teb_controller/teb_local_planner_plugin.xml` |
| 默认参数文件 | `venom_teb_controller/params/teb_params.yaml` |

在 VNV 分层里，它属于 `planning/navigation/`，负责局部路径跟踪、避障与轨迹优化，不负责 waypoint、行为树或任务调度。

## 与 Nav2 的关系

当前包通过 `package.xml` 导出：

```xml
<nav2_core plugin="${prefix}/teb_local_planner_plugin.xml" />
```

插件 XML 中声明的 controller 类型为：

```xml
teb_local_planner::TebLocalPlannerROS
```

因此它的使用方式是把参数合入 Nav2 的 `controller_server`，而不是把它当作独立 launch 入口直接启动。

当前参数文件里使用的 Nav2 controller 配置入口是：

```yaml
controller_server:
  ros__parameters:
    controller_plugins: ["FollowPath"]
    controller_plugin_types: ["teb_local_planner::TebLocalPlannerROS"]
    FollowPath:
      plugin: teb_local_planner::TebLocalPlannerROS
```

## 输入与输出

| 方向 | 接口 | 说明 |
| --- | --- | --- |
| 输入 | Nav2 全局路径 | 由 Nav2 planner / BT 流程传入 controller server |
| 输入 | `/odom` | 当前参数文件中 `odom_topic` 默认使用 `/odom` |
| 输入 | costmap | 由 Nav2 controller server 提供局部障碍物与代价地图 |
| 输出 | `cmd_vel` | 由 Nav2 controller server 统一对外发布速度命令 |
| 输出 | TEB feedback / visualization | 受 `publish_feedback` 等参数控制 |

## 当前没有独立 launch

仓库中这个子模块当前没有提供独立 `.launch.py` 文件。正确接入点是：

1. 在 Nav2 参数文件中加入或替换 `controller_server` 的 controller 插件配置
2. 确认 `teb_local_planner` 与 `teb_msgs` 已经编译进入工作区
3. 通过上层 bringup 启动 Nav2，再由 Nav2 加载 TEB controller

这也是为什么文档和 Makefile 把它归到 `planning/navigation/`，而不是 `venom_bringup` 或 `mission/`。

## 参数说明

| 参数名 | 作用 | 默认值 |
| --- | --- | --- |
| `controller_frequency` | Nav2 controller server 调用 controller 的频率，单位 Hz。 | `5.0` |
| `odom_topic` | controller 使用的里程计话题。 | `/odom` |
| `controller_plugins` | Nav2 controller server 加载的插件实例名。 | `["FollowPath"]` |
| `controller_plugin_types` | controller 插件类型。 | `["teb_local_planner::TebLocalPlannerROS"]` |
| `teb_autosize` | 是否自动调整 TEB 轨迹离散点数量。 | `1.0` |
| `dt_ref` | 相邻轨迹点的目标时间间隔，单位秒。 | `0.3` |
| `dt_hysteresis` | 时间分辨率调整的滞回范围。 | `0.1` |
| `max_samples` | TEB 轨迹允许的最大采样点数量。 | `500` |
| `max_global_plan_lookahead_dist` | 从全局路径中截取给局部优化器的最大前视距离，单位米。 | `3.0` |
| `global_plan_viapoint_sep` | 从全局路径抽取 via-point 的间距，单位米。 | `0.3` |
| `global_plan_prune_distance` | 已走过全局路径的裁剪距离，单位米。 | `1.0` |
| `max_vel_x` | 机器人前向最大线速度，单位 m/s。 | `0.26` |
| `max_vel_theta` | 机器人最大角速度，单位 rad/s。 | `1.0` |
| `acc_lim_x` | 前向线加速度限制，单位 m/s²。 | `2.5` |
| `acc_lim_theta` | 角加速度限制，单位 rad/s²。 | `3.2` |
| `footprint_model.type` | 机器人足迹模型类型。 | `"circular"` |
| `footprint_model.radius` | 圆形足迹半径，单位米。 | `0.17` |
| `free_goal_vel` | 到达目标时是否允许非零速度。 | `False` |
| `min_obstacle_dist` | 轨迹与障碍物的最小期望距离，单位米。 | `0.27` |
| `inflation_dist` | 障碍物膨胀影响距离，单位米。 | `0.6` |
| `include_costmap_obstacles` | 是否把 costmap 障碍物纳入优化。 | `True` |
| `include_dynamic_obstacles` | 是否启用动态障碍物相关项。 | `True` |
| `costmap_converter_plugin` | costmap 转多边形插件名称。 | `costmap_converter::CostmapToPolygonsDBSMCCH` |
| `no_inner_iterations` | 单次外层循环中的内层优化次数。 | `5` |
| `no_outer_iterations` | 每次 controller 调用中的外层优化次数。 | `4` |
| `optimization_activate` | 是否启用优化器。 | `True` |
| `penalty_epsilon` | 软约束惩罚函数的缓冲量。 | `0.1` |
| `weight_max_vel_x` | 前向速度约束权重。 | `0.5` |
| `weight_max_vel_theta` | 角速度约束权重。 | `0.5` |
| `weight_acc_lim_x` | 线加速度约束权重。 | `0.5` |
| `weight_acc_lim_theta` | 角加速度约束权重。 | `10.5` |
| `weight_kinematics_nh` | 非完整约束权重。 | `1000.0` |
| `weight_kinematics_forward_drive` | 倾向前进运动的权重。 | `3.0` |
| `weight_optimaltime` | 轨迹时间最优项权重。 | `1.0` |
| `weight_obstacle` | 障碍物距离代价权重。 | `100.0` |
| `weight_viapoint` | 贴近全局路径 via-point 的权重。 | `50.0` |
| `enable_homotopy_class_planning` | 是否启用同伦类多候选路径规划。 | `True` |
| `enable_multithreading` | 同伦类搜索是否使用多线程。 | `True` |
| `max_number_classes` | 最多保留的同伦类候选数量。 | `4` |
| `shrink_horizon_backup` | 发生不可行轨迹时是否缩短规划视野。 | `True` |
| `oscillation_recovery` | 是否启用振荡恢复逻辑。 | `True` |

## 接入边界

- `venom_teb_controller` 只作为 Nav2 controller 插件被加载
- 上层任务目标由 `mission/navigation/` 负责下发
- 地图、costmap 与机器人足迹由 Nav2 参数和机器人描述共同约束
- 若启用 `costmap_converter_plugin`，运行环境必须具备对应插件依赖；否则应在具体 Nav2 参数中关闭或替换该插件

## 相关页面

- [规划层](index.md)
- [总体架构](../architecture.md)
- [仿真层](../simulation/index.md)
- [任务层](../mission/index.md)
