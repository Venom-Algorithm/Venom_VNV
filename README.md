# Venom VNV

基于 ROS 2 Humble 的 RoboMaster 机器人系统，集成定位建图、重定位、导航与自瞄能力。

## 系统架构

```
┌─────────────────────────────────────────────────────┐
│                   感知层 Perception                   │
│         海康相机 (ros2_hik_camera)                    │
│              ↓ /image_raw                            │
│     装甲板检测 (armor_detector) → 目标跟踪 (armor_tracker) │
│              ↓ /tracker/target                       │
│     弹道解算 (auto_aim_solver) → /auto_aim            │
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
│  串口通信 (venom_serial_driver) ←→ DJI C 板           │
│  底盘驱动 (scout_ros2 + ugv_sdk) ←→ Scout Mini       │
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
| `venom_serial_driver` | [HY-LiYihan](https://github.com/HY-LiYihan/venom_serial_driver) | NUC 与 DJI C 板串口通信，双向二进制协议，CRC16 校验 |

### 激光里程计 (`lio/`)

| 子模块 | 来源 | 说明 |
|--------|------|------|
| `Point-LIO` | [HY-LiYihan](https://github.com/HY-LiYihan/Point-LIO) | 高带宽激光惯性里程计，4k-8kHz 输出频率，抗 IMU 饱和与剧烈振动 |
| `rf2o_laser_odometry` | [HY-LiYihan](https://github.com/HY-LiYihan/rf2o_laser_odometry) | 基于 Range Flow 的 2D 激光扫描里程计，计算极快（0.9ms） |

### 重定位 (`relocalization/`)

| 子模块 | 来源 | 说明 |
|--------|------|------|
| `small_gicp_relocalization` | [HY-LiYihan](https://github.com/HY-LiYihan/small_gicp_relocalization) | 基于 small_gicp 的点云重定位，计算 map→odom 变换 |

### 自瞄算法 (`rm_auto_aim/`)

| 子模块 | 来源 | 说明 |
|--------|------|------|
| `rm_auto_aim` | [HY-LiYihan](https://github.com/HY-LiYihan/rm_auto_aim) | RoboMaster 自瞄算法套件，含 4 个子包：`armor_detector`（检测）、`armor_tracker`（EKF 跟踪）、`auto_aim_solver`（弹道解算）、`auto_aim_interfaces`（消息定义） |

### 系统集成（非子模块）

| 目录 | 说明 |
|------|------|
| `venom_bringup/` | 系统启动入口 + 通用任务控制框架（Mission Controller），支持状态监控、任务中断恢复、插件化架构 |
| `venom_robot_description/` | TF 树发布包，YAML 配置静态/动态 TF，支持从 `/robot_status` 读取角度发布动态 TF |

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
# 克隆主仓库及子模块
git clone --recurse-submodules git@github.com:Venom-Algorithm/Venom_VNV.git
cd Venom_VNV

# 安装依赖
rosdep install --from-paths . --ignore-src -r -y

# 编译
colcon build --symlink-install -DCMAKE_BUILD_TYPE=Release
```

> 详细的装配与配置步骤见 [文档站](https://venom-algorithm.github.io/Venom_VNV/setup)

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
| [装配配置](https://venom-algorithm.github.io/Venom_VNV/setup) | Livox-SDK 安装、工作空间编译、网卡 IP 配置、MID360 配置 |
| [话题参考](https://venom-algorithm.github.io/Venom_VNV/topics) | 系统级 ROS2 话题、数据流图、自定义消息字段 |
| [TF 树](https://venom-algorithm.github.io/Venom_VNV/tf_tree) | 坐标系层级结构与帧说明 |
| [串口驱动](https://venom-algorithm.github.io/Venom_VNV/venom_serial_driver) | venom_serial_driver 话题、协议与测试 |
| [Point-LIO](https://venom-algorithm.github.io/Venom_VNV/point_lio) | Point-LIO 配置步骤与依赖安装 |
| [重定位](https://venom-algorithm.github.io/Venom_VNV/small_gicp_relocalization) | small_gicp 重定位模块说明 |
| [自瞄算法](https://venom-algorithm.github.io/Venom_VNV/rm_auto_aim) | 自瞄数据流与启动方式 |
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
