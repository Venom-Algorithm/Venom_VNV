"""
Mission Controller Package - 通用任务控制框架

提供状态监控、任务管理和行为插件系统，支持：
- 通用状态监控器（可监控任意 ROS 话题）
- 任务状态保存和恢复
- 插件化行为系统
- 配置化触发条件

使用示例:
    from mission_controller import StateMonitor, MissionManager
    from plugins import HealthPlugin
    
    monitor = StateMonitor()
    manager = MissionManager()
    health = HealthPlugin(monitor, manager)
    health.setup(low_threshold=0.2, high_threshold=1.0)
"""

from .state_monitor import StateMonitor
from .mission_manager import MissionManager, MissionState
from .behavior_plugins import (
    BehaviorPlugin,
    ReturnToBaseBehavior,
    PauseMissionBehavior,
    ContinueMissionBehavior,
    BehaviorContext
)

__all__ = [
    'StateMonitor',
    'MissionManager',
    'MissionState',
    'BehaviorPlugin',
    'ReturnToBaseBehavior',
    'PauseMissionBehavior',
    'ContinueMissionBehavior',
    'BehaviorContext',
]

__version__ = '1.0.0'
