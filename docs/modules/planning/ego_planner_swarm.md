---
title: Ego Planner Swarm
description: ego-planner-swarm - ROS 2 版本无人机局部规划与集群规划子模块。
---

## 模块定位

`planning/navigation/ego-planner-swarm` 是从 ZJU FAST Lab 上游接入的 ROS 2 规划子模块，当前跟踪 `ros2_version` 分支。

它属于规划层，负责无人机局部轨迹生成、避障与集群规划验证，不负责 waypoint 任务编排、行为树或状态监听。

## 目录位置

```text
planning/navigation/ego-planner-swarm
```

当前 `.gitmodules` 中对应配置：

```text
url = https://github.com/ZJU-FAST-Lab/ego-planner-swarm.git
branch = ros2_version
```

## 主要子包

| 子目录 | 作用 |
| --- | --- |
| `src/planner/plan_manage` | 规划主流程与 launch 入口 |
| `src/planner/plan_env` | 局部地图与环境表达 |
| `src/planner/path_searching` | 路径搜索 |
| `src/planner/bspline_opt` | B 样条轨迹优化 |
| `src/planner/traj_utils` | 轨迹消息与工具 |
| `src/uav_simulator/*` | 上游自带的无人机仿真与地图生成工具 |

## DDS 要求

上游 README 明确建议使用 CycloneDDS，避免默认 FastDDS 下出现明显卡顿。

安装：

```bash
sudo apt install ros-humble-rmw-cyclonedds-cpp
```

临时切换当前终端：

```bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
```

长期写入 shell：

```bash
echo "export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp" >> ~/.bashrc
source ~/.bashrc
```

验证：

```bash
ros2 doctor --report | grep "RMW middleware"
```

## 常用启动命令

启动 RViz：

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch ego_planner rviz.launch.py
```

单机仿真：

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch ego_planner single_run_in_sim.launch.py
```

集群仿真：

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch ego_planner swarm.launch.py
```

大规模集群仿真：

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch ego_planner swarm_large.launch.py
```

带可选参数启动：

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch ego_planner single_run_in_sim.launch.py use_mockamap:=True use_dynamic:=False
```

参数说明：

| 参数 | 作用 | 默认值 |
| --- | --- | --- |
| `use_mockamap` | 地图生成方式。`False` 使用 Random Forest，`True` 使用 mockamap。 | `False` |
| `use_dynamic` | 是否考虑动态约束。 | `False` |

## 与 VNV 架构的边界

- `ego-planner-swarm` 只放在 `planning/navigation/`
- waypoint、任务切换、全局状态监听应放在 `mission/`
- PX4 外部位姿桥接应通过 `driver/venom_px4_bridge` 和 `venom_bringup` 组织

## 相关页面

- [规划层](index.md)
- [PX4 Bridge](../drivers/venom_px4_bridge.md)
- [启动使用](../../home/launch_usage.md)
