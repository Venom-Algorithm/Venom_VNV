# venom_bringup

系统启动配置包 + 通用任务控制框架（Mission Controller）。

## 启动文件

| Launch 文件 | 功能 |
|-------------|------|
| `autoaim_test_bringup.launch.py` | 自瞄测试（相机 + 自瞄 + 串口） |
| `autoaim_nav_bringup.launch.py` | 导航 + 自瞄（完整模式） |
| `mapping_bringup.launch.py` | 3D + 2D 建图 |
| `relocalization_bringup.launch.py` | 重定位 |
| `health_aware_navigation.launch.py` | 血量感知导航 |

## Mission Controller — 通用任务控制框架

### 核心特性

- **通用状态监控** — 可监控任意 ROS 话题（血量、电池、视觉等）
- **插件化架构** — 轻松扩展新的监控类型和行为
- **任务状态持久化** — 支持中断后精确恢复任务状态
- **配置驱动** — 通过 YAML 配置，无需修改代码

### 架构

```
┌──────────────────────────────────────┐
│       Generic Mission Controller     │
│  ┌──────────────┐ ┌───────────────┐ │
│  │State Monitor │→│Mission Manager│ │
│  └──────────────┘ └───────────────┘ │
└──────────────────────────────────────┘
        ↓                    ↓
  Health Plugin      Navigation Plugin
  (血量监控)          (导航任务)
```

### 快速使用

```bash
# 血量感知导航（默认配置）
ros2 launch venom_bringup health_aware_navigation.launch.py

# 自定义航点文件
ros2 run venom_bringup multi_waypoint_commander \
    --ros-args -p waypoints_file:=/path/to/waypoints.yaml

# 自定义任务配置
ros2 run venom_bringup multi_waypoint_commander \
    --ros-args -p mission_config_file:=/path/to/mission_config.yaml
```

### 任务状态

| 状态 | 说明 |
|------|------|
| `IDLE` | 空闲 |
| `RUNNING` | 正在执行 |
| `PAUSED` | 已暂停 |
| `EMERGENCY` | 紧急状态（如血量低） |
| `COMPLETED` | 已完成 |
| `FAILED` | 已失败 |

状态转换：`IDLE → RUNNING → COMPLETED`，`RUNNING → EMERGENCY → RUNNING（恢复）`

## 详细文档

详见：[MISSION_CONTROLLER_README.md](../venom_bringup/MISSION_CONTROLLER_README.md)
