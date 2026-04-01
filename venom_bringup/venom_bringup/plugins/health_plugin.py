"""
Health Plugin - 血量监控插件

演示如何使用通用框架实现具体的业务插件：
- 血量百分比监控
- 低血量自动返回基地
- 血量恢复后继续任务
- 任务状态保存和恢复

使用示例:
    from plugins import HealthPlugin
    
    health = HealthPlugin(state_monitor, mission_manager, navigator)
    health.setup(
        low_threshold=0.2,      # 20% 血量时返回
        high_threshold=1.0,     # 100% 血量时恢复
        base_position=PoseStamped(x=0.0, y=0.0)
    )
"""

from typing import Any, Callable, Dict, Optional
from geometry_msgs.msg import PoseStamped
from venom_bringup.msg import GameStatus
from mission_controller.state_monitor import StateMonitor
from mission_controller.mission_manager import MissionManager, MissionState
from mission_controller.behavior_plugins import (
    BehaviorContext,
    ReturnToBaseBehavior,
    ContinueMissionBehavior
)
import time


class HealthPlugin:
    """
    血量监控插件
    
    功能:
    - 订阅 /game_status 话题获取血量信息
    - 血量低于阈值时自动返回基地
    - 血量恢复到阈值后继续未完成的的任务
    - 保存和恢复任务状态（当前航点、方向等）
    """
    
    def __init__(
        self,
        state_monitor: StateMonitor,
        mission_manager: MissionManager,
        navigator: Any = None
    ):
        """
        初始化血量插件
        
        Args:
            state_monitor: 状态监控器实例
            mission_manager: 任务管理器实例
            navigator: 导航器实例（用于自动返回）
        """
        self.state_monitor = state_monitor
        self.mission_manager = mission_manager
        self.navigator = navigator
        
        self._low_threshold = 0.2
        self._high_threshold = 1.0
        self._base_position: Optional[PoseStamped] = None
        
        self._is_initialized = False
        self._last_hp_percentage = 0.0
        self._was_low_health = False
        self._was_recovered = False
        
        self._return_behavior: Optional[ReturnToBaseBehavior] = None
        self._continue_behavior: Optional[ContinueMissionBehavior] = None
        
        if hasattr(state_monitor, 'get_logger'):
            self.state_monitor.get_logger().info('HealthPlugin initialized')
    
    def setup(
        self,
        low_threshold: float = 0.2,
        high_threshold: float = 1.0,
        base_position: Optional[PoseStamped] = None,
        mission_id: str = 'navigation'
    ):
        """
        配置血量监控
        
        Args:
            low_threshold: 低血量阈值（0.0-1.0），默认 20%
            high_threshold: 高血量阈值（0.0-1.0），默认 100%
            base_position: 基地位置（返回点）
            mission_id: 任务 ID
        """
        self._low_threshold = low_threshold
        self._high_threshold = high_threshold
        self._base_position = base_position
        self._mission_id = mission_id
        
        self._setup_monitors()
        self._setup_behaviors()
        
        self._is_initialized = True
        
        if hasattr(self.state_monitor, 'get_logger'):
            self.state_monitor.get_logger().info(
                f'HealthPlugin setup: low={low_threshold}, high={high_threshold}'
            )
    
    def _setup_monitors(self):
        """设置血量监控器"""
        def on_low_health(value: float):
            self._on_low_health(value)
        
        def on_health_recovered(value: float):
            self._on_health_recovered(value)
        
        self.state_monitor.add_monitor(
            name='low_health',
            topic='/game_status',
            msg_type=GameStatus,
            field='hp_percentage',
            condition=lambda v: v < self._low_threshold and v > 0.0,
            on_trigger=on_low_health,
            cooldown=5.0
        )
        
        self.state_monitor.add_monitor(
            name='health_recovered',
            topic='/game_status',
            msg_type=GameStatus,
            field='hp_percentage',
            condition=lambda v: v >= self._high_threshold,
            on_trigger=on_health_recovered,
            cooldown=5.0
        )
    
    def _setup_behaviors(self):
        """设置行为插件"""
        def on_arrive_at_base():
            self._on_arrive_at_base()
        
        self._return_behavior = ReturnToBaseBehavior(
            base_position=self._base_position,
            on_arrive=on_arrive_at_base,
            navigator=self.navigator
        )
        
        def on_continue():
            self._on_continue_mission()
        
        self._continue_behavior = ContinueMissionBehavior(
            on_continue=on_continue
        )
    
    def _on_low_health(self, hp_percentage: float):
        """低血量触发逻辑"""
        if self._was_low_health:
            return
        
        self._was_low_health = True
        self._was_recovered = False
        self._last_hp_percentage = hp_percentage
        
        if hasattr(self.state_monitor, 'get_logger'):
            self.state_monitor.get_logger().warning(
                f'Low health detected: {hp_percentage:.1%}, returning to base...'
            )
        
        self._save_mission_state()
        
        self.mission_manager.transition_to(
            self._mission_id,
            MissionState.EMERGENCY
        )
        
        if self._return_behavior:
            context = BehaviorContext(
                mission_id=self._mission_id,
                mission_data={'base_position': self._base_position}
            )
            self._return_behavior.execute(context)
    
    def _on_health_recovered(self, hp_percentage: float):
        """血量恢复触发逻辑"""
        if not self._was_low_health or self._was_recovered:
            return
        
        self._was_recovered = True
        self._was_low_health = False
        self._last_hp_percentage = hp_percentage
        
        if hasattr(self.state_monitor, 'get_logger'):
            self.state_monitor.get_logger().info(
                f'Health recovered: {hp_percentage:.1%}, resuming mission...'
            )
        
        self.mission_manager.transition_to(
            self._mission_id,
            MissionState.RUNNING
        )
    
    def _on_arrive_at_base(self):
        """到达基地后的处理"""
        if hasattr(self.state_monitor, 'get_logger'):
            self.state_monitor.get_logger().info('Arrived at base, waiting for health recovery...')
    
    def _on_continue_mission(self):
        """继续任务时的处理"""
        if hasattr(self.state_monitor, 'get_logger'):
            self.state_monitor.get_logger().info('Continuing mission from saved state')
    
    def _save_mission_state(self):
        """保存任务状态"""
        state_data = {
            'interrupted': True,
            'interrupt_time': time.time(),
            'interrupt_reason': 'low_health',
            'health_at_interrupt': self._last_hp_percentage
        }
        
        self.mission_manager.save_state(self._mission_id, state_data)
    
    def save_navigation_state(
        self,
        current_waypoint: int,
        total_waypoints: int,
        direction: str = 'forward',
        waypoint_data: Optional[Dict] = None
    ):
        """
        保存导航状态
        
        Args:
            current_waypoint: 当前航点索引
            total_waypoints: 总航点数
            direction: 方向（forward/return）
            waypoint_data: 航点详细数据
        """
        state_data = {
            'current_waypoint': current_waypoint,
            'total_waypoints': total_waypoints,
            'direction': direction,
            'waypoint_data': waypoint_data,
            'interrupted': True,
            'interrupt_time': time.time(),
            'interrupt_reason': 'low_health',
            'health_at_interrupt': self._last_hp_percentage
        }
        
        self.mission_manager.save_state(self._mission_id, state_data)
        
        if hasattr(self.state_monitor, 'get_logger'):
            self.state_monitor.get_logger().info(
                f'Saved navigation state: waypoint={current_waypoint}/{total_waypoints}, '
                f'direction={direction}'
            )
    
    def restore_navigation_state(self) -> Optional[Dict[str, Any]]:
        """
        恢复导航状态
        
        Returns:
            恢复的状态数据字典，如果未保存则返回 None
        """
        state_data = self.mission_manager.restore_state(self._mission_id)
        
        if state_data is None:
            return None
        
        if not state_data.get('interrupted', False):
            return None
        
        if hasattr(self.state_monitor, 'get_logger'):
            self.state_monitor.get_logger().info(
                f'Restored navigation state: waypoint={state_data.get("current_waypoint")}, '
                f'direction={state_data.get("direction")}'
            )
        
        return state_data
    
    def is_returning(self) -> bool:
        """是否正在返回基地"""
        if self._return_behavior is None:
            return False
        return self._return_behavior.is_returning()
    
    def check_arrival_at_base(self, current_position, current_waypoint: int) -> bool:
        """
        检查是否到达基地
        
        Args:
            current_position: 当前位置 (x, y)
            current_waypoint: 当前航点索引
            
        Returns:
            bool: 是否到达基地
        """
        if self._return_behavior is None:
            return False
        return self._return_behavior.check_arrival(current_position, current_waypoint)
    
    def get_health_percentage(self) -> float:
        """获取当前血量百分比"""
        return self._last_hp_percentage
    
    def is_low_health(self) -> bool:
        """是否处于低血量状态"""
        return self._last_hp_percentage < self._low_threshold
    
    def is_full_health(self) -> bool:
        """是否满血"""
        return self._last_hp_percentage >= self._high_threshold
    
    def was_interrupted(self) -> bool:
        """任务是否曾被中断"""
        return self._was_low_health
    
    def was_recovered(self) -> bool:
        """任务是否已恢复"""
        return self._was_recovered and not self._was_low_health
    
    def reset(self):
        """重置插件状态"""
        self._was_low_health = False
        self._was_recovered = False
        self._last_hp_percentage = 0.0
        
        if hasattr(self.state_monitor, 'get_logger'):
            self.state_monitor.get_logger().info('HealthPlugin reset')
    
    def get_status(self) -> Dict[str, Any]:
        """获取插件状态信息"""
        return {
            'initialized': self._is_initialized,
            'low_threshold': self._low_threshold,
            'high_threshold': self._high_threshold,
            'current_health': self._last_hp_percentage,
            'is_low_health': self.is_low_health(),
            'is_full_health': self.is_full_health(),
            'was_interrupted': self._was_low_health,
            'was_recovered': self._was_recovered,
            'is_returning': self.is_returning()
        }
