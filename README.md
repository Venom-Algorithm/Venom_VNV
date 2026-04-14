# Venom VNV

基于 ROS 2 Humble 的综合通用无人系统平台，面向 RoboMaster、CUADC、RoboTac、智能无人系统、机器人及人工智能等各类比赛场景，支持导航、抓取、自瞄以及无人车、无人机、无人船等多平台集成。

## 项目定位

Venom VNV 的目标不是只服务单一赛事，而是沉淀一套可复用、可迁移、可快速部署的机器人系统底座。

它希望在不同比赛任务和不同机器人载体之间，复用以下能力：

- 感知接入
- 定位建图
- 全局重定位
- 导航与任务控制
- 机械执行与串口通信
- 抓取与操作任务扩展
- 自瞄与目标跟踪任务扩展

当前平台重点覆盖以下载体和任务方向：

- 无人车
- 无人机
- 无人船
- 通用移动机器人

核心设计思路是：

- 用统一工作空间组织不同能力模块
- 用 submodule 管理可独立维护的功能仓库
- 用一致的 ROS 2 接口约束系统耦合方式
- 用通用 bringup 和任务控制框架支撑不同比赛模式

## 平台能力概览

```
┌─────────────────────────────────────────────────────┐
│                   感知层 Perception                   │
│         海康相机 (ros2_hik_camera)                    │
│              ↓ /image_raw                            │
│     目标检测 / 跟踪 / 抓取 / 自瞄等任务模块             │
├─────────────────────────────────────────────────────┤
│                   定位层 Localization                 │
│  Livox Mid360 (livox_ros_driver2)                    │
│       ↓ /livox/lidar                                 │
│  3D 里程计 (Point-LIO) ──→ 重定位 (small_gicp_reloc)  │
│  2D 里程计 (rf2o_laser_odometry)                      │
├─────────────────────────────────────────────────────┤
│                   决策层 Decision                     │
│  Mission Controller (venom_bringup)                   │
│  状态监控 · 任务中断恢复 · 插件化行为                   │
├─────────────────────────────────────────────────────┤
│                   执行层 Actuation                    │
│  串口 / CAN / 自定义执行机构接口                       │
│  底盘 / 飞控 / 船体平台适配                            │
└─────────────────────────────────────────────────────┘
```

## 子模块一览

### 硬件驱动 (`driver/`)

| 子模块 | 来源 | 说明 |
|--------|------|------|
| `livox_ros_driver2` | [Livox-SDK](https://github.com/Livox-SDK/livox_ros_driver2) | Livox 激光雷达驱动（Mid360 / HAP），需先安装 [Livox-SDK2](https://github.com/Livox-SDK/Livox-SDK2) |
| `ros2_hik_camera` | [HY-LiYihan](https://github.com/HY-LiYihan/ros2_hik_camera) | 海康 USB3.0 工业相机驱动，SDK 内嵌，支持 amd64/arm64 |
| `scout_ros2` | [AgileX](https://github.com/agilexrobotics/scout_ros2) | Scout / Scout Mini 底盘 ROS2 控制包（含 scout_base, scout_description, scout_msgs） |
| `ugv_sdk` | [AgileX](https://github.com/agilexrobotics/ugv_sdk) | 通用 C++ 移动平台通信库，CAN 总线接口，支持 Scout/Hunter/Bunker 等 |
| `venom_serial_driver` | [Venom-Algorithm](https://github.com/Venom-Algorithm/venom_serial_driver) | NUC 与控制板串口通信，双向二进制协议，适合作为通用执行接口 |

### 激光里程计 (`lio/`)

| 子模块 | 来源 | 说明 |
|--------|------|------|
| `Point-LIO` | [Venom-Algorithm](https://github.com/Venom-Algorithm/Point-LIO) | 高带宽激光惯性里程计，可作为多类无人平台的主定位输入 |
| `rf2o_laser_odometry` | [Venom-Algorithm](https://github.com/Venom-Algorithm/rf2o_laser_odometry) | 基于 Range Flow 的 2D 激光扫描里程计 |

### 重定位 (`relocalization/`)

| 子模块 | 来源 | 说明 |
|--------|------|------|
| `small_gicp_relocalization` | [Venom-Algorithm](https://github.com/Venom-Algorithm/small_gicp_relocalization) | 基于 small_gicp 的点云重定位，计算 map→odom 变换 |

### 自瞄算法 (`rm_auto_aim/`)

| 子模块 | 来源 | 说明 |
|--------|------|------|
| `rm_auto_aim` | [Venom-Algorithm](https://github.com/Venom-Algorithm/rm_auto_aim) | 目标检测、跟踪与解算能力模块，可服务 RoboMaster 等打击任务场景 |

### 系统集成（非子模块）

| 目录 | 说明 |
|------|------|
| `venom_bringup/` | 系统启动入口 + 通用任务控制框架（Mission Controller），适配不同比赛模式与任务组合 |
| `venom_robot_description/` | TF 树发布包，支持不同机器人本体的静态/动态坐标组织 |

## 目录结构

```
venom_vnv/
├── driver/                          # 硬件驱动
│   ├── livox_ros_driver2/           # Livox 激光雷达驱动
│   ├── ros2_hik_camera/             # 海康工业相机驱动
│   ├── scout_ros2/                  # Scout 底盘驱动
│   ├── ugv_sdk/                     # 通用移动平台 SDK
│   └── venom_serial_driver/         # C 板串口通信驱动
├── lio/                             # 激光里程计
│   ├── Point-LIO/                   # 3D 激光惯性里程计
│   └── rf2o_laser_odometry/         # 2D 激光里程计
├── relocalization/                  # 重定位
│   └── small_gicp_relocalization/   # 点云重定位
├── rm_auto_aim/                     # 自瞄算法
│   ├── armor_detector/              # 装甲板检测
│   ├── armor_tracker/               # 目标跟踪
│   ├── auto_aim_solver/             # 弹道解算
│   └── auto_aim_interfaces/         # 消息定义
├── venom_bringup/                   # 系统启动 + 任务控制框架
├── venom_robot_description/         # 机器人 TF 描述
├── docs/                            # 项目文档
└── assets/                          # 文档图片资源
```

## 快速开始

### 环境要求

- Ubuntu 22.04
- ROS 2 Humble
- Livox-SDK2（Point-LIO 依赖）

### 克隆与编译

```bash
rm -rf ~/venom_ws
mkdir -p ~/venom_ws/src
git clone --recurse-submodules https://github.com/Venom-Algorithm/Venom_VNV ~/venom_ws/src/venom_vnv
cp ~/venom_ws/src/venom_vnv/driver/livox_ros_driver2/package_ROS2.xml \
   ~/venom_ws/src/venom_vnv/driver/livox_ros_driver2/package.xml
cd ~/venom_ws
rosdep install -r --from-paths src --ignore-src --rosdistro $ROS_DISTRO -y
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release -DROS_EDITION=ROS2 -DHUMBLE_ROS=humble
```

> 详细部署与配置步骤见文档站首页：[venom-algorithm.github.io/Venom_VNV](https://venom-algorithm.github.io/Venom_VNV/)

### 常用启动命令

```bash
source install/setup.bash

# 自瞄测试（相机 + 自瞄 + 串口）
ros2 launch venom_bringup autoaim_test_bringup.launch.py

# 导航 + 自瞄（完整模式）
ros2 launch venom_bringup autoaim_nav_bringup.launch.py

# 建图（3D + 2D）
ros2 launch venom_bringup mapping_bringup.launch.py

# 重定位
ros2 launch venom_bringup relocalization_bringup.launch.py
```

## 文档索引

> 📖 完整文档站：[venom-algorithm.github.io/Venom_VNV](https://venom-algorithm.github.io/Venom_VNV/)

| 文档 | 说明 |
|------|------|
| [快速开始](https://venom-algorithm.github.io/Venom_VNV/quick_start) | 工作空间初始化、依赖安装与标准编译流程 |
| [环境准备](https://venom-algorithm.github.io/Venom_VNV/environment) | Ubuntu、SSH、ROS、rosdep、VS Code、Clash、NoMachine |
| [配置雷达](https://venom-algorithm.github.io/Venom_VNV/lidar_setup) | Livox-SDK 安装、MID360 网络与配置文件设置 |
| [底盘 CAN 部署](https://venom-algorithm.github.io/Venom_VNV/chassis_can_setup) | Scout Mini 底盘 CAN 接口初始化与调试 |
| [rc.local](https://venom-algorithm.github.io/Venom_VNV/rc_local) | 开机自启动与网络优先级配置 |
| [话题参考](https://venom-algorithm.github.io/Venom_VNV/topics) | 系统级 ROS2 话题、数据流图、自定义消息字段 |
| [TF 树](https://venom-algorithm.github.io/Venom_VNV/tf_tree) | 坐标系层级结构与帧说明 |
| [串口驱动](https://venom-algorithm.github.io/Venom_VNV/venom_serial_driver) | 串口接口、协议与测试 |
| [Point-LIO](https://venom-algorithm.github.io/Venom_VNV/point_lio) | Point-LIO 相关说明 |
| [重定位](https://venom-algorithm.github.io/Venom_VNV/small_gicp_relocalization) | small_gicp 重定位模块说明 |
| [自瞄算法](https://venom-algorithm.github.io/Venom_VNV/rm_auto_aim) | 检测、跟踪与解算能力模块说明 |
| [装甲板检测](https://venom-algorithm.github.io/Venom_VNV/armor_detector) | armor_detector 模块说明 |
| [目标跟踪](https://venom-algorithm.github.io/Venom_VNV/armor_tracker) | armor_tracker 模块说明 |

## 数据流

```
相机 ──/image_raw──→ armor_detector ──/detector/armors──→ armor_tracker
                                                         │
                                                         ↓ /tracker/target
                                                    auto_aim_solver
                                                         │
                                                         ↓ /auto_aim
Livox Mid360 ──/livox/lidar──→ Point-LIO ──/odom──→  venom_serial_driver ──UART──→ C板
                                  │                        ↑
                                  ↓                        │ /venom_cmd_vel
                          small_gicp_reloc            Nav2 / Teleop
                              (map→odom)
```

## License

各子模块遵循各自的开源协议，详见各子目录下的 LICENSE 文件。
