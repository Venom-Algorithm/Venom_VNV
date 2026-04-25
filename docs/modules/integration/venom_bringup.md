---
title: 系统启动
description: venom_bringup — 系统启动配置与任务控制框架。
---

## 模块定位

`venom_bringup` 是整仓库的系统层入口，负责：

- 组织多模块联合启动
- 管理不同运行模式的 launch 组合
- 将导航、自瞄、定位、驱动等模块拼装成完整系统
- 作为当前历史阶段下的任务层逻辑挂载点

如果说单个 pkg 解决的是“一个模块怎么跑”，那么 `venom_bringup` 解决的是“整套系统怎么协同跑”。

按当前冻结架构，后续新增的 waypoint、行为树、监听器、任务发布这类包，不应继续默认塞进 `venom_bringup`，而应逐步收敛到 `mission/` 层。

## 主要启动入口

| 启动文件 | 功能 |
| --- | --- |
| `camera.launch.py` | 单独验证相机链路 |
| `mid360_rviz.launch.py` | Mid360 驱动与 RViz 可视化验证 |
| `mid360_point_lio.launch.py` | Mid360 + Point-LIO 联调 |
| `d435i_test.launch.py` | RealSense D435i 验证 |
| `infantry_auto_aim.launch.py` | 步兵自瞄链路（相机 + 自瞄 + 串口） |
| `scout_mini_mapping.launch.py` | Scout Mini 建图与导航链路联调 |
| `sentry_mapping.launch.py` | 哨兵建图与导航链路联调 |
| `relocalization_bringup.launch.py` | 重定位模式 |
| `health_aware_navigation.launch.py` | 带任务层状态感知的导航模式 |
| `px4_agent_probe.launch.py` | PX4 DDS Agent 探测 |
| `px4_vps_bridge.launch.py` | PX4 外部位姿 / VPS 里程计桥接 |
| `robot_bringup.launch.py` | 顶层整机入口 |

## 参数与配置入口

`venom_bringup` 的参数不是集中在单个 yaml，而是分成几类：

- 机器人专项配置：`config/scout_mini/`、`config/sentry/`、`config/infantry/`
- 相机参数：`config/*/camera_params.yaml`
- 自瞄参数：`config/*/node_params.yaml`
- 串口参数：`config/*/serial_params.yaml`
- LIO 参数透传：`config/*/point_lio_mapping.yaml`
- 导航参数：`config/*/nav2_params.yaml`
- 任务控制参数：`mission_config.yaml`、`waypoints.yaml`

也就是说，`venom_bringup` 更像“参数调度中心”，而不是单独定义某个算法参数的地方。

## 核心职责

- launch 编排：定义模块之间的启动顺序与组合关系
- 模式切换：同一套仓库支持测试、比赛、联调等不同运行模式
- 任务控制：通过任务控制器管理任务状态和恢复逻辑
- 参数整合：将多包参数放在统一入口调度

## 任务控制器

当前 `venom_bringup` 还承载了通用任务控制框架，主要用于：

- 监控任务状态
- 根据外部状态触发暂停、恢复、重试等行为
- 支持任务持久化与中断恢复

任务控制器当前最直接的参数入口是：

- [`mission_config.yaml`](https://github.com/Venom-Algorithm/Venom_VNV/blob/master/venom_bringup/config/scout_mini/mission_config.yaml)
- [`waypoints.yaml`](https://github.com/Venom-Algorithm/Venom_VNV/blob/master/venom_bringup/config/scout_mini/waypoints.yaml)

运行时代码入口包括：

- [`health_aware_commander.py`](https://github.com/Venom-Algorithm/Venom_VNV/blob/master/venom_bringup/venom_bringup/health_aware_commander.py)
- [`multi_waypoint_commander.py`](https://github.com/Venom-Algorithm/Venom_VNV/blob/master/venom_bringup/venom_bringup/multi_waypoint_commander.py)

其中最关键的两个外部参数是：

| 参数名 | 作用 | 默认语义 |
| --- | --- | --- |
| `waypoints_file` | 航点文件路径。 | 指向当前机器人对应的航点配置 |
| `mission_config_file` | 任务配置文件路径。 | 指向当前机器人对应的任务配置 |

## 推荐使用方式

日常使用尽量从 `venom_bringup` 进入，而不是直接逐个启动底层模块：

```bash
# Mid360 + Point-LIO 联调
ros2 launch venom_bringup mid360_point_lio.launch.py

# 步兵自瞄链路
ros2 launch venom_bringup infantry_auto_aim.launch.py
```

如果是整机入口，更建议使用：

```bash
ros2 launch venom_bringup robot_bringup.launch.py
```

它会根据 `robot_type` 选择不同平台的 bringup 组合。

## 调试重点

- 单模块能跑但整机起不来时，优先检查 bringup 里传入的参数文件路径
- 出现 TF、话题重名或重复启动，优先检查 launch 组合关系
- 不同机器人切换时，首先确认 `robot_type` 和对应配置目录是否一致

## 相关页面

- [启动与使用](../../home/launch_usage.md)
- [运行模式](../../deployment/run_modes.md)
- [自瞄算法总览](../auto_aim/index.md)
- [定位模块总览](../localization/index.md)

## 进一步阅读

- [MISSION_CONTROLLER_README.md](https://github.com/Venom-Algorithm/Venom_VNV/blob/master/venom_bringup/MISSION_CONTROLLER_README.md)
