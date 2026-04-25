---
title: 快速开始
description: 面向第一次使用者的最短上手路径。
---

## 开始之前

请先确认以下工具已经可用：

- Ubuntu 22.04
- ROS 2 Humble
- `rosdep`
- `colcon`
- Livox-SDK2

如果你的 Ubuntu、ROS 2 Humble、`rosdep`、VS Code 等基础环境还没有准备好，请先参考 [环境准备](../deployment/environment.md)。

可以先用下面的方式确认 Livox-SDK2 已安装：

```bash
ldconfig -p | grep LivoxSdkCore
```

如果还没有安装，请先参考 [雷达配置](../deployment/lidar_setup.md) 完成 Livox-SDK2 安装。

如果 `rosdep install` 过程中报错，建议先尝试：

```bash
sudo rosdep init
rosdep update
```

## 拉取仓库

首次拉取推荐使用以下命令：

```bash
cd ~
mkdir -p ~/venom_ws/src
git clone --recurse-submodules https://github.com/Venom-Algorithm/Venom_VNV ~/venom_ws/src/venom_vnv
```

如果你只需要某一类功能，也可以先不递归拉取全部子模块，再按 profile 拉取：

```bash
cd ~
mkdir -p ~/venom_ws/src
git clone https://github.com/Venom-Algorithm/Venom_VNV ~/venom_ws/src/venom_vnv
cd ~/venom_ws/src/venom_vnv
make submodules-ugv       # 无人车真机：底盘、雷达、定位、感知
make submodules-sim       # 纯仿真：仿真工作区与规划
make submodules-ugv-sim   # 无人车仿真：仿真、定位、规划、YOLO
make submodules-auto-aim  # 自瞄开发：感知、相机、串口
make submodules-uav       # 无人机：PX4 桥接与 Ego Planner
make submodules-all       # 全量拉取所有子模块
```

第一次部署整套系统时仍推荐使用 `--recurse-submodules` 全量拉取；开发单个方向时再用上面的按需拉取方式节省时间和磁盘。

如果你之前有旧工作区，建议先清理后重新拉取：

注意：如果你当前终端正好停留在 `~/venom_ws` 或它的子目录里，删除前请先切回家目录，否则删完后当前 shell 会处在一个失效路径中，后续 `git` 可能报 `Unable to read current working directory`。

```bash
cd ~
rm -rf ~/venom_ws
mkdir -p ~/venom_ws/src
git clone --recurse-submodules https://github.com/Venom-Algorithm/Venom_VNV ~/venom_ws/src/venom_vnv
```

## 编译工作区

拉取完成后，按以下流程完成首次编译：

```bash
cp ~/venom_ws/src/venom_vnv/driver/livox_ros_driver2/package_ROS2.xml \
   ~/venom_ws/src/venom_vnv/driver/livox_ros_driver2/package.xml

cd ~/venom_ws
rosdep install -r --from-paths src --ignore-src --rosdistro $ROS_DISTRO -y
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release -DROS_EDITION=ROS2 -DHUMBLE_ROS=humble
```

编译完成后：

```bash
source ~/venom_ws/install/setup.bash
```

## 更新到远端最新版本

如果你已经拉过仓库，后续可用下面的命令同步主仓库和子模块：

```bash
cd ~/venom_ws/src/venom_vnv
git pull
git submodule sync --recursive
git submodule update --init --recursive
```

如果你是按需拉取的工作区，更新后可以重新执行对应 profile，例如：

```bash
cd ~/venom_ws/src/venom_vnv
git pull
git submodule sync --recursive
make submodules-uav
```

如果你需要配置开发机上的 Git 远端地址规则，请继续阅读 [开发说明](../support/development.md).

## 推荐阅读顺序

1. [环境准备](../deployment/environment.md)
2. [雷达配置](../deployment/lidar_setup.md)
3. [底盘 CAN 部署](../deployment/chassis_can_setup.md)
4. [启动使用](launch_usage.md)

## 首次验证

- 雷达链路：参考 [Livox 雷达驱动](../modules/drivers/livox_ros_driver2.md)
- 相机链路：参考 [海康相机驱动](../modules/drivers/ros2_hik_camera.md)
- 串口链路：参考 [串口通信驱动](../modules/drivers/venom_serial_driver.md)
- 系统级数据流：参考 [话题与 TF 总览](../deployment/system_overview.md)
