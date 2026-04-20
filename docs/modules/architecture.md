---
title: 总体架构
permalink: /architecture
desc: 从系统层面理解驱动、感知、定位、规划、系统与仿真的整体分层。
breadcrumb: 模块与接口
layout: default
---

## 六层结构

1. 驱动层：各类硬件驱动、底层 SDK 与桥接接口
2. 感知层：检测、识别、跟踪、自瞄与通用视觉模块
3. 定位层：LIO、里程计、重定位与地图对齐
4. 规划层：局部/全局规划、避障、轨迹生成
5. 系统层：系统启动、机器人描述、模式编排与任务组织
6. 仿真层：与主工作区解耦的仿真工作区和回归环境

## 当前目录映射

| 层级 | 主要目录 | 说明 |
| --- | --- | --- |
| 驱动层 | `driver/` | 传感器、底盘、机械臂、串口、PX4 接入 |
| 感知层 | `perception/` | 自瞄、通用目标检测等感知算法 |
| 定位层 | `localization/` | LIO、2D 里程计、重定位 |
| 规划层 | `planning/`（预留） | 预留给 `ego_planner` 一类的规划算法 |
| 系统层 | `venom_bringup`、`venom_robot_description` | 系统启动、描述、任务编排 |
| 仿真层 | `simulation/venom_nav_simulation` | 独立仿真工作区和导航联调环境 |

## 设计原则

- 驱动层只负责把硬件能力接进 ROS 2 图谱
- 感知层只负责从传感器数据中提取结构化目标信息
- 定位层只负责姿态、里程计和全局对齐
- 规划层只负责轨迹与路径，不直接承载任务逻辑
- 系统层负责把这些模块组织成完整运行模式
- 仿真层与主工作区解耦，避免仿真资产污染真实部署链路

## 建议阅读顺序

- [驱动层]({{ '/driver_overview' | relative_url }})
- [感知层]({{ '/perception_overview' | relative_url }})
- [定位层]({{ '/localization_overview' | relative_url }})
- [规划层]({{ '/planning_overview' | relative_url }})
- [系统层]({{ '/integration_overview' | relative_url }})
- [仿真层]({{ '/simulation_overview' | relative_url }})
