# Mission Controller Framework - 通用任务控制框架

## 📚 概述

这是一个高度通用化的 ROS2 任务控制框架，专为自主导航任务设计，支持状态监控、任务中断和恢复功能。

### 核心特性

- ✅ **通用状态监控** - 可监控任意 ROS 话题，不局限于血量
- ✅ **插件化架构** - 轻松扩展新的监控类型和行为
- ✅ **任务状态持久化** - 支持中断后精确恢复任务状态
- ✅ **配置驱动** - 通过 YAML 配置，无需修改代码
- ✅ **多场景复用** - 适用于血量、电池、视觉等多种监控场景

---

## 🏗️ 架构设计

```
┌─────────────────────────────────────────────────────┐
│           Generic Mission Controller                │
├─────────────────────────────────────────────────────┤
│  ┌──────────────────┐    ┌─────────────────────┐   │
│  │ State Monitor    │───▶│  Mission Manager    │   │
│  │ (状态监控器)     │    │  (任务管理器)        │   │
│  └──────────────────┘    └─────────────────────┘   │
└─────────────────────────────────────────────────────┘
         │                           │
         ▼                           ▼
┌─────────────────┐         ┌──────────────────┐
│ Health Plugin   │         │ Navigation Plugin│
│ (血量插件)      │         │ (导航插件)        │
└─────────────────┘         └──────────────────┘
```

---

## 📁 目录结构

```
venom_bringup/
├── venom_bringup/
│   ├── mission_controller/
│   │   ├── __init__.py
│   │   ├── state_monitor.py          # 通用状态监控器
│   │   ├── mission_manager.py        # 任务管理器
│   │   └── behavior_plugins.py       # 行为插件
│   │
│   ├── plugins/
│   │   ├── __init__.py
│   │   ├── health_plugin.py          # 血量监控插件
│   │   └── navigation_plugin.py      # 导航任务插件
│   │
│   └── health_aware_commander.py     # 血量感知指挥官
│
├── config/
│   └── scout_mini/
│       ├── waypoints.yaml            # 航点配置
│       └── mission_config.yaml       # 任务配置
│
└── launch/
    └── health_aware_navigation.launch.py  # 启动文件
```

---

## 🚀 快速开始

### 1. 基本使用（血量监控导航）

```bash
# 使用默认配置启动
ros2 launch venom_bringup health_aware_navigation.launch.py

# 或者运行节点
ros2 run venom_bringup multi_waypoint_commander
```

### 2. 自定义配置文件

```bash
# 指定航点文件
ros2 run venom_bringup multi_waypoint_commander \
    --ros-args -p waypoints_file:=/path/to/waypoints.yaml

# 指定任务配置文件
ros2 run venom_bringup multi_waypoint_commander \
    --ros-args -p mission_config_file:=/path/to/mission_config.yaml
```

---

## 💡 使用示例

### 示例 1: 简单的血量监控

```python
from mission_controller import StateMonitor, MissionManager
from plugins import HealthPlugin

# 初始化
monitor = StateMonitor()
manager = MissionManager(node)
health = HealthPlugin(monitor, manager, navigator)

# 配置血量监控（20% 返回，100% 恢复）
health.setup(
    low_threshold=0.2,
    high_threshold=1.0,
    base_position=PoseStamped(x=0.0, y=0.0)
)

# 启动导航
nav_plugin = NavigationPlugin(navigator, manager)
nav_plugin.load_waypoints_from_file(waypoints_file)
nav_plugin.start_mission(loop=True)
```

### 示例 2: 多条件监控（血量 + 电池）

```python
# 添加血量监控
monitor.add_monitor(
    name='low_health',
    topic='/game_status',
    msg_type=GameStatus,
    field='hp_percentage',
    condition=lambda v: v < 0.2,
    on_trigger=on_low_health
)

# 添加电池监控
monitor.add_monitor(
    name='low_battery',
    topic='/battery_status',
    msg_type=BatteryState,
    field='percentage',
    condition=lambda v: v < 0.15,
    on_trigger=on_low_battery
)

# 添加自定义监控（例如：敌人检测）
monitor.add_monitor(
    name='enemy_detected',
    topic='/vision/detections',
    msg_type=Detections,
    field='detections',
    condition=lambda dets: any(d.class_id == ENEMY for d in dets),
    on_trigger=enter_combat_mode
)
```

### 示例 3: 自定义行为插件

```python
from mission_controller.behavior_plugins import BehaviorPlugin, BehaviorContext

class CustomBehavior(BehaviorPlugin):
    def execute(self, context: BehaviorContext) -> bool:
        # 实现自定义行为
        print(f"Executing custom behavior for mission: {context.mission_id}")
        return True

# 注册行为
manager.register_behavior(
    MissionState.EMERGENCY,
    lambda mission_id: custom_behavior.execute(
        BehaviorContext(mission_id=mission_id)
    )
)
```

---

## 📖 配置说明

### mission_config.yaml 配置项

#### 1. 状态监控器配置

```yaml
monitors:
  health:
    enabled: true
    topic: "/game_status"
    msg_type: "venom_bringup/msg/GameStatus"
    field: "hp_percentage"
    conditions:
      - name: "low_health"
        type: "threshold"
        operator: "<"
        value: 0.2
        action: "return_to_base"
        cooldown: 5.0
```

#### 2. 行为插件配置

```yaml
behaviors:
  return_to_base:
    plugin: "ReturnToBaseBehavior"
    params:
      base_position:
        x: 0.0
        y: 0.0
      tolerance: 0.5
```

#### 3. 任务配置

```yaml
mission:
  type: "waypoint_navigation"
  waypoints_file: "config/scout_mini/waypoints.yaml"
  loop: true
  save_state_on_interrupt: true
  restore_on_recovery: true
```

---

## 🔧 API 参考

### StateMonitor

```python
class StateMonitor(Node):
    def add_monitor(name, topic, msg_type, field, condition, on_trigger, cooldown=0.0)
    def remove_monitor(name)
    def enable_monitor(name)
    def disable_monitor(name)
    def get_monitor_value(name) -> Any
    def get_all_values() -> Dict[str, Any]
```

### MissionManager

```python
class MissionManager:
    def create_mission(mission_id, initial_state)
    def save_state(mission_id, state_data)
    def restore_state(mission_id) -> Dict
    def transition_to(mission_id, new_state)
    def get_state(mission_id) -> MissionState
    def register_behavior(state, behavior)
```

### HealthPlugin

```python
class HealthPlugin:
    def setup(low_threshold, high_threshold, base_position, mission_id)
    def save_navigation_state(current_waypoint, total_waypoints, direction)
    def restore_navigation_state() -> Dict
    def is_low_health() -> bool
    def is_full_health() -> bool
    def is_returning() -> bool
```

---

## 🎯 应用场景

### 1. 血量监控导航（当前实现）
- 血量 < 20% → 返回基地
- 血量 = 100% → 恢复任务

### 2. 电池监控
- 电池 < 15% → 返回充电
- 电池 = 100% → 继续任务

### 3. 通信监控
- 信号丢失 → 执行紧急程序
- 信号恢复 → 继续任务

### 4. 视觉监控
- 检测到目标 → 执行特定行为
- 目标丢失 → 恢复巡逻

---

## 📝 任务状态说明

### MissionState 枚举

- `IDLE` - 空闲状态
- `RUNNING` - 正在执行
- `PAUSED` - 已暂停
- `EMERGENCY` - 紧急状态
- `COMPLETED` - 已完成
- `FAILED` - 已失败

### 状态转换流程

```
IDLE → RUNNING → COMPLETED
              ↘
               EMERGENCY → RUNNING (恢复)
```

---

## 🛠️ 开发指南

### 创建自定义插件

1. 继承 `BehaviorPlugin` 基类
2. 实现 `execute` 方法
3. 在配置文件中注册

```python
class MyPlugin(BehaviorPlugin):
    def execute(self, context: BehaviorContext) -> bool:
        # 你的逻辑
        return True
```

### 添加新的监控类型

```python
monitor.add_monitor(
    name='my_monitor',
    topic='/my_topic',
    msg_type=MyMsgType,
    field='my_field',
    condition=lambda v: v > threshold,
    on_trigger=my_callback
)
```

---

## ❓ 常见问题

### Q: 如何修改血量阈值？
A: 在 `mission_config.yaml` 中修改 `health_plugin.low_threshold` 和 `high_threshold`

### Q: 如何更改返回点位置？
A: 修改配置文件中的 `mission.base_position` 或在代码中设置 `base_position`

### Q: 如何禁用循环导航？
A: 设置 `mission.loop: false` 或在启动时指定参数

### Q: 如何在其他程序中复用？
A: 导入 `mission_controller` 和 `plugins` 模块，按照示例代码初始化即可

---

## 📞 技术支持

如有问题，请查看：
- 代码注释文档
- 配置文件示例
- 测试代码示例

---

## 📄 许可证

本项目遵循项目主目录中的许可证条款。
