---
title: 导航仿真工作区
permalink: /venom_nav_simulation
desc: venom_nav_simulation — MID360、Gazebo、LIO 与 Nav2 联调用的独立仿真工作区。
breadcrumb: 仿真层
layout: default
---

## 模块定位

`simulation/venom_nav_simulation` 是一个独立 ROS 2 仿真工作区，主要用于：

- 模拟 Livox MID-360 与 IMU
- 验证 `Point-LIO` 或 `Fast-LIO`
- 验证 `Nav2`
- 在进入真实机器人前先跑通定位与导航链路

## 主要能力

- Gazebo 小车仿真
- 模拟 MID-360 点云输出
- 模拟 IMU 输出
- `Point-LIO` / `Fast-LIO` 联调
- `Nav2` 建图与导航流程验证

## 当前布局

```text
simulation/venom_nav_simulation/
├── src/rm_nav_bringup
├── src/rm_navigation
├── src/rm_localization
├── src/rm_perception
└── src/rm_simulation/venom_mid360_simulation
```

## 典型用途

1. 仿真建图
2. 已知地图导航验证
3. LIO 参数回归
4. Nav2 行为调试

## 快速开始

```bash
cd simulation/venom_nav_simulation
rosdep install -r --from-paths src --ignore-src --rosdistro $ROS_DISTRO -y
colcon build --symlink-install
source install/setup.bash
ros2 launch rm_nav_bringup bringup_sim.launch.py \
  world:=RMUL \
  mode:=nav \
  lio:=pointlio \
  localization:=slam_toolbox \
  lio_rviz:=False \
  nav_rviz:=True
```

## 为什么不直接放进主工作区

这是一个独立的仿真工作区，不建议直接并进主部署工作区，原因是：

- 依赖链更重
- 资源文件更多
- 仿真 launch 和真实机器人 launch 的组织方式不同

它更适合作为仿真基线，而不是主部署入口。

## 相关页面

- [仿真层]({{ '/simulation_overview' | relative_url }})
- [定位层]({{ '/localization_overview' | relative_url }})
- [规划层]({{ '/planning_overview' | relative_url }})
