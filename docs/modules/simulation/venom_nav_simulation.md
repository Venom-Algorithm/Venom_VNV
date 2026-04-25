---
title: 导航仿真工作区
description: venom_nav_simulation — MID360、Gazebo、LIO 与 Nav2 联调用的独立仿真工作区。
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

## Docker 方式

如果只是想使用主仓库提供的统一 sim 环境，可以在主仓库根目录执行：

```bash
cd ~/venom_ws/src/venom_vnv
make build
make up
make shell
```

进入容器后：

```bash
cd /ros_ws
source /opt/ros/humble/setup.bash
rosdep install -r --from-paths src --ignore-src --rosdistro humble -y
colcon build --cmake-args -DCMAKE_BUILD_TYPE=Release -DROS_EDITION=ROS2 -DHUMBLE_ROS=humble
```

也可以直接使用封装命令：

```bash
cd ~/venom_ws/src/venom_vnv
make rosdep
make colcon
```

本地复现 CI 构建：

```bash
cd ~/venom_ws/src/venom_vnv
make ci-build
```

当前 Docker 镜像基于 `ros:humble-ros-base`，包含 Ignition Fortress、Nav2、RViz2、PCL、OpenCV、YOLO 运行依赖等。CI 会跳过硬件驱动和 Gazebo Classic 相关包。

## 为什么不直接放进主工作区

这是一个独立的仿真工作区，不建议直接并进主部署工作区，原因是：

- 依赖链更重
- 资源文件更多
- 仿真 launch 和真实机器人 launch 的组织方式不同

它更适合作为仿真基线，而不是主部署入口。

## 相关页面

- [仿真层](index.md)
- [定位层](../localization/index.md)
- [规划层](../planning/index.md)
