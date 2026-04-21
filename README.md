<div align="center">

# Venom VNV

基于 ROS 2 Humble 的综合通用无人系统平台，用统一工作空间组织导航、抓取、自瞄、定位、仿真与多载体系统集成能力。

<p>
  <a href="./README.md">
    <img src="https://img.shields.io/badge/README-%E4%B8%AD%E6%96%87-111111?style=for-the-badge" alt="README 中文">
  </a>
  <a href="./README_EN.md">
    <img src="https://img.shields.io/badge/README-English-2563eb?style=for-the-badge" alt="README English">
  </a>
</p>

<p>
  <a href="https://venom-algorithm.github.io/Venom_VNV/">
    <img src="https://img.shields.io/badge/Docs-%E4%B8%AD%E6%96%87-c2410c?style=flat-square" alt="Docs 中文">
  </a>
  <a href="https://venom-algorithm.github.io/Venom_VNV/en/">
    <img src="https://img.shields.io/badge/Docs-English-1d4ed8?style=flat-square" alt="Docs English">
  </a>
  <img src="https://img.shields.io/badge/Ubuntu-22.04-E95420?style=flat-square&logo=ubuntu&logoColor=white" alt="Ubuntu 22.04">
  <img src="https://img.shields.io/badge/ROS%202-Humble-22314E?style=flat-square&logo=ros&logoColor=white" alt="ROS 2 Humble">
</p>

</div>

## 项目定位

Venom VNV 不是单一赛题工程，而是面向多种机器人载体和任务形态的统一底座。当前重点覆盖：

- 无人车
- 无人机
- 无人船
- 通用移动机器人

目标是把不同方向里重复出现的工程问题沉淀成统一能力：

- 传感器接入与硬件驱动
- 目标检测、跟踪、自瞄与任务感知
- LIO、里程计与重定位
- 路径规划、controller 与机械臂运动规划
- waypoint、行为树、监听器与任务管理
- 系统启动与接口约束
- 导航仿真与回归验证

## 快速入口

- 文档首页：[venom-algorithm.github.io/Venom_VNV](https://venom-algorithm.github.io/Venom_VNV/)
- 快速开始：[Quick Start / 快速开始](https://venom-algorithm.github.io/Venom_VNV/quick_start)
- 模块与接口：[Modules & Interfaces / 模块与接口](https://venom-algorithm.github.io/Venom_VNV/interface_reference)
- 开发说明：[Development Notes / 开发说明](https://venom-algorithm.github.io/Venom_VNV/development)
- 英文文档：[venom-algorithm.github.io/Venom_VNV/en](https://venom-algorithm.github.io/Venom_VNV/en/)

## 七层结构

| 层级 | 主要目录 | 说明 |
| --- | --- | --- |
| 驱动层 | `driver/` | Livox、海康相机、底盘、机械臂、串口、PX4 桥接 |
| 感知层 | `perception/` | 自瞄检测、跟踪、解算等任务感知链路 |
| 定位层 | `localization/` | Point-LIO、Fast-LIO、rf2o、small_gicp 重定位 |
| 规划层 | `planning/` | 导航 planner、controller 与 MoveIt 抓取规划一类算法入口 |
| 任务层 | `mission/` | `venom_waypoint`、行为树、监听器、任务管理一类包的统一入口 |
| 系统层 | `venom_bringup`、`venom_robot_description` | 系统启动、模式组织、TF 描述与整机装配 |
| 仿真层 | `simulation/venom_nav_simulation` | 面向导航与定位链路的独立仿真工作区 |

## 核心模块

| 分类 | 代表模块 | 说明 |
| --- | --- | --- |
| 传感器与驱动 | `livox_ros_driver2`、`ros2_hik_camera`、`venom_serial_driver` | 激光雷达、工业相机、串口链路接入 |
| 载体驱动 | `scout_ros2`、`hunter_ros2`、`ugv_sdk`、`piper_ros` | 底盘、移动平台 SDK 与机械臂链路 |
| 飞控桥接 | `driver/venom_px4_bridge` | PX4、DDS Agent 与 ROS 2 桥接 |
| 感知 | `perception/rm_auto_aim` | 检测、跟踪、解算及接口定义 |
| 定位 | `Point-LIO`、`Fast-LIO`、`rf2o_laser_odometry` | 3D/2D 里程计输出与统一接口约束 |
| 重定位 | `small_gicp_relocalization` | 基于点云配准恢复 `map -> odom` |
| 规划 | `planning/` | `venom_eagle_planner`、`venom_teb_controller`、`venom_moveit_grasp` 等规划算法入口 |
| 任务 | `mission/` | `venom_waypoint`、`venom_nav_bt`、`venom_global_monitor`、`venom_mission_manager` 等任务包入口 |
| 系统集成 | `venom_bringup` | 统一启动入口与整机装配组织 |
| 机器人描述 | `venom_robot_description` | 机器人模型、URDF 与 TF 发布 |
| 仿真 | `venom_nav_simulation` | `MID360 + Gazebo + LIO + Nav2` 联调环境 |

## 仓库结构

```text
venom_vnv/
├── driver/                          # 驱动层
│   ├── livox_ros_driver2/
│   ├── ros2_hik_camera/
│   ├── scout_ros2/
│   ├── hunter_ros2/
│   ├── ugv_sdk/
│   ├── piper_ros/
│   ├── venom_px4_bridge/
│   └── venom_serial_driver/
├── perception/                      # 感知层
│   └── rm_auto_aim/
├── localization/                    # 定位层
│   ├── lio/
│   │   ├── Point-LIO/
│   │   ├── Fast-LIO/
│   │   └── rf2o_laser_odometry/
│   └── relocalization/
│       └── small_gicp_relocalization/
├── planning/                        # 规划层
│   ├── navigation/                  # 导航规划与 controller
│   └── manipulation/                # 机械臂运动规划
├── mission/                         # 任务层
│   ├── navigation/                  # waypoint、BT、任务监听
│   └── manipulation/                # 抓取任务流程
├── venom_bringup/                   # 系统层：启动与整机装配
├── venom_robot_description/         # 系统层：机器人描述与 TF
├── simulation/
│   └── venom_nav_simulation/        # 仿真层
├── docs/                            # GitHub Pages 文档
└── assets/                          # README / 文档图片资源
```

## 快速开始

### 环境基线

- Ubuntu 22.04
- ROS 2 Humble
- `rosdep`
- `colcon`
- Livox-SDK2

如果 ROS、`rosdep`、VS Code 或 Livox-SDK2 还没准备好，先看：

- [环境准备](https://venom-algorithm.github.io/Venom_VNV/environment)
- [雷达配置](https://venom-algorithm.github.io/Venom_VNV/lidar_setup)

### 克隆与编译

如果你之前有旧工作区，建议先切回家目录再清理，避免当前 shell 停在一个已删除路径里。

```bash
cd ~
rm -rf ~/venom_ws
mkdir -p ~/venom_ws/src
git clone --recurse-submodules https://github.com/Venom-Algorithm/Venom_VNV ~/venom_ws/src/venom_vnv

cp ~/venom_ws/src/venom_vnv/driver/livox_ros_driver2/package_ROS2.xml \
   ~/venom_ws/src/venom_vnv/driver/livox_ros_driver2/package.xml

cd ~/venom_ws
rosdep install -r --from-paths src --ignore-src --rosdistro $ROS_DISTRO -y
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release -DROS_EDITION=ROS2 -DHUMBLE_ROS=humble
```

如果 `rosdep` 出错，可以先尝试：

```bash
sudo rosdep init
rosdep update
```

## 常用启动命令

```bash
cd ~/venom_ws
source install/setup.bash

# Mid360 + RViz 验证
ros2 launch venom_bringup mid360_rviz.launch.py

# Mid360 + Point-LIO
ros2 launch venom_bringup mid360_point_lio.launch.py

# 步兵自瞄链路
ros2 launch venom_bringup infantry_auto_aim.launch.py

# Scout Mini 建图
ros2 launch venom_bringup scout_mini_mapping.launch.py

# PX4 DDS 探测
ros2 launch venom_bringup px4_agent_probe.launch.py
```

更多命令见：

- [启动使用](https://venom-algorithm.github.io/Venom_VNV/launch_usage)
- [运行模式](https://venom-algorithm.github.io/Venom_VNV/run_modes)

## 文档导航

| 文档 | 说明 |
| --- | --- |
| [快速开始](https://venom-algorithm.github.io/Venom_VNV/quick_start) | 工作区初始化、依赖安装与标准编译流程 |
| [环境准备](https://venom-algorithm.github.io/Venom_VNV/environment) | Ubuntu、ROS、rosdep、VS Code、开发机基础环境 |
| [雷达配置](https://venom-algorithm.github.io/Venom_VNV/lidar_setup) | MID360 网络、配置文件与 Livox-SDK2 |
| [启动使用](https://venom-algorithm.github.io/Venom_VNV/launch_usage) | 常用 build、重编译与启动命令 |
| [模块与接口](https://venom-algorithm.github.io/Venom_VNV/interface_reference) | 驱动、感知、定位、规划、任务、系统、仿真等模块入口 |
| [话题参考](https://venom-algorithm.github.io/Venom_VNV/topics) | 统一 ROS 2 话题与消息约束 |
| [TF 树](https://venom-algorithm.github.io/Venom_VNV/tf_tree) | 系统核心坐标系与 TF 关系 |
| [开发说明](https://venom-algorithm.github.io/Venom_VNV/development) | 开发环境、Git、fork / PR、子模块协作规则 |

## 开发协作

当前推荐协作模型：

```text
fork -> clone -> branch -> commit -> push -> Pull Request -> review -> merge
```

默认建议：

- 主仓库默认中文 README
- 英文 README 与英文文档同时维护
- 代码修改优先走 fork / PR
- 子模块改动先在子模块仓库提 PR，再回主仓库更新指针

详细说明见：

- [开发说明](https://venom-algorithm.github.io/Venom_VNV/development)
- [贡献指南](https://venom-algorithm.github.io/Venom_VNV/contributing)

## License

主仓库中的各个子模块遵循各自的开源协议，具体以对应目录内的 `LICENSE` 文件为准。
