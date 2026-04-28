---
title: Venom VNV
description: 面向多载体机器人系统的通用平台，支持导航、抓取、自瞄与多模块协同。
---

## 项目定位

Venom VNV 是一个基于 ROS 2 Humble 构建的综合通用平台。

项目目标是提供一个尽可能到手即用的统一底座，用于支持：

- 导航
- 抓取
- 自瞄
- 无人车
- 无人机
- 无人船

通过统一的驱动层、感知层、定位层、规划层、任务层、系统层、仿真层与接口规范，降低不同赛事和不同平台之间的迁移成本。

当前仓库并不只服务于单一比赛项目，而是希望沉淀一套可复用的基础工程能力，覆盖：

- 激光雷达、相机、串口、底盘、机械臂等硬件接入
- 自瞄检测、通用目标检测、跟踪、解算等感知链路
- LIO、里程计、重定位等定位与地图能力
- 轨迹规划、controller 与机械臂运动规划
- 行为树、waypoint、任务监听与任务管理
- 多车型、多任务形态下的统一启动与接口规范

## 快速开始

<div class="card-grid" data-toc-exclude>
  <a href="home/quick_start/" class="card" style="text-decoration:none">
    <h3>⚙️ 快速开始</h3>
    <p>按标准流程拉取仓库、安装依赖并完成首次编译。</p>
  </a>
  <a href="deployment/environment/" class="card" style="text-decoration:none">
    <h3>🧰 环境配置</h3>
    <p>准备 Ubuntu、SSH、ROS、rosdep、VS Code、Clash 与 NoMachine。</p>
  </a>
  <a href="deployment/lidar_setup/" class="card" style="text-decoration:none">
    <h3>📡 雷达配置</h3>
    <p>安装 Livox-SDK2、配置 MID360 网络参数并验证雷达链路。</p>
  </a>
  <a href="home/launch_usage/" class="card" style="text-decoration:none">
    <h3>🚀 启动使用</h3>
    <p>查看常用 build、重编译和整机启动命令。</p>
  </a>
  <a href="deployment/chassis_can_setup/" class="card" style="text-decoration:none">
    <h3>🛞 底盘 CAN 部署</h3>
    <p>初始化底盘 CAN 适配器，拉起接口并完成基础验证。</p>
  </a>
  <a href="deployment/piper_can_setup/" class="card" style="text-decoration:none">
    <h3>🦾 机械臂 CAN 部署</h3>
    <p>识别 Piper CAN 模块、命名接口并启动机械臂链路。</p>
  </a>
  <a href="deployment/rc_local/" class="card" style="text-decoration:none">
    <h3>🔁 rc.local</h3>
    <p>配置开机自启动与网络优先级相关命令。</p>
  </a>
  <a href="deployment/run_modes/" class="card" style="text-decoration:none">
    <h3>🧭 运行模式</h3>
    <p>查看不同联调、测试与整机模式下的使用方式。</p>
  </a>
  <a href="deployment/system_overview/" class="card" style="text-decoration:none">
    <h3>🧩 话题与 TF 总览</h3>
    <p>快速查看系统级话题接口与核心 TF 约定。</p>
  </a>
</div>

## 项目组成总览

当前仓库由主仓库内置包和外部子模块两部分组成。为了方便总览，首页统一按“分类 / 地址 / 说明”展示如下：

<table class="home-overview-table">
  <thead>
    <tr>
      <th>分类</th>
      <th>地址</th>
      <th>说明</th>
    </tr>
  </thead>
  <tbody>
    <tr><td>驱动层</td><td><code>driver/livox_ros_driver2</code></td><td>Livox Mid360 激光雷达驱动与点云发布</td></tr>
    <tr><td>驱动层</td><td><code>driver/ros2_hik_camera</code></td><td>海康 USB3.0 工业相机驱动</td></tr>
    <tr><td>驱动层</td><td><code>driver/venom_serial_driver</code></td><td>NUC 与下位机之间的串口通信驱动</td></tr>
    <tr><td>驱动层</td><td><code>driver/scout_ros2</code></td><td>AgileX Scout / Scout Mini 系列底盘 ROS 2 驱动封装</td></tr>
    <tr><td>驱动层</td><td><code>driver/hunter_ros2</code></td><td>AgileX Hunter 系列底盘 ROS 2 驱动封装</td></tr>
    <tr><td>驱动层</td><td><code>driver/ugv_sdk</code></td><td>AgileX / Weston Robot 通用底盘 C++ SDK 与 CAN 工具脚本</td></tr>
    <tr><td>驱动层</td><td><code>driver/piper_ros</code></td><td>AgileX Piper 机械臂 ROS 2 控制、描述、MoveIt 与仿真接口</td></tr>
    <tr><td>驱动层</td><td><code>driver/venom_px4_bridge</code></td><td>PX4 集成项目根目录，内部包含 vendored <code>px4_msgs</code> 与自有桥接包</td></tr>
    <tr><td>感知层</td><td><code>perception/rm_auto_aim</code></td><td>自瞄能力总包，包含检测、跟踪、解算与接口定义</td></tr>
    <tr><td>感知层</td><td><code>perception/yolo_detector</code></td><td>通用 YOLO 2D 目标检测模块与自定义消息定义</td></tr>
    <tr><td>感知层</td><td><code>perception/zbar_ros</code></td><td>基于 ZBar 的二维码 / 条码识别模块，输出结构化识别结果</td></tr>
    <tr><td>感知层</td><td><code>perception/rm_auto_aim/armor_detector</code></td><td>装甲板检测模块</td></tr>
    <tr><td>感知层</td><td><code>perception/rm_auto_aim/armor_tracker</code></td><td>目标跟踪模块</td></tr>
    <tr><td>感知层</td><td><code>perception/rm_auto_aim/auto_aim_solver</code></td><td>弹道与目标解算模块</td></tr>
    <tr><td>感知层</td><td><code>perception/rm_auto_aim/auto_aim_interfaces</code></td><td>自瞄链路使用的消息与接口定义</td></tr>
    <tr><td>定位层</td><td><code>localization/lio/Point-LIO</code></td><td>高带宽激光惯性里程计，适合 Mid360 等高频点云输入</td></tr>
    <tr><td>定位层</td><td><code>localization/lio/Fast-LIO</code></td><td>FAST-LIO 的 ROS 2 版本实现</td></tr>
    <tr><td>定位层</td><td><code>localization/lio/rf2o_laser_odometry</code></td><td>面向 2D 激光雷达的里程计模块</td></tr>
    <tr><td>定位层</td><td><code>localization/relocalization/small_gicp_relocalization</code></td><td>基于点云配准的重定位模块</td></tr>
    <tr><td>规划层</td><td><code>planning/navigation/ego-planner-swarm</code></td><td>无人机局部规划与集群规划子模块，跟踪上游 <code>ros2_version</code> 分支</td></tr>
    <tr><td>规划层</td><td><code>planning/manipulation</code></td><td>机械臂运动规划一类模块的统一入口，目前保留占位</td></tr>
    <tr><td>任务层</td><td><code>mission/</code></td><td>waypoint、行为树、状态监听、任务下发与任务管理一类模块的统一入口，已创建 <code>navigation/</code> 与 <code>manipulation/</code> 占位目录</td></tr>
    <tr><td>系统层</td><td><code>venom_bringup</code></td><td>系统启动入口，负责模式组织、整机装配与联调，不直接承载新任务包</td></tr>
    <tr><td>系统层</td><td><code>venom_robot_description</code></td><td>机器人模型、URDF、TF 发布与基础描述配置</td></tr>
    <tr><td>仿真层</td><td><code>simulation/venom_nav_simulation</code></td><td>独立导航仿真工作区，用于 MID360、LIO 与 Nav2 联调</td></tr>
  </tbody>
</table>

### 文档与接口规范

| 内容 | 说明 |
|------|------|
| 部署与使用 | 面向环境准备、雷达配置、底盘部署、开机自启与运行模式 |
| 模块与接口 | 面向驱动、感知、定位、规划、任务、系统、仿真与统一接口规范 |
| 支持与社区 | 面向 FAQ、故障排查、迁移记录、联系方式与协作说明 |

## 阅读建议

如果你是第一次接触这个仓库，建议按以下顺序阅读：

1. 从“快速开始”了解标准拉取、依赖安装与编译流程
2. 从“环境准备”和“雷达配置”完成基础部署
3. 从“模块与接口”进入对应模块，查看具体输入输出、参数与约束
