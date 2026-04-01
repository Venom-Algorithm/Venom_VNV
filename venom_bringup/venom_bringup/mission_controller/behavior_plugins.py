"""
Behavior Plugins - 行为插件接口和内置实现

提供行为插件的抽象基类和常用行为实现：
- ReturnToBaseBehavior: 返回基地行为
- PauseMissionBehavior: 暂停任务行为
- ContinueMissionBehavior: 继续任务行为
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
from geometry_msgs.msg import PoseStamped
import time


@dataclass
class BehaviorContext:
    """行为执行上下文"""
    mission_id: str
    mission_data: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get(self, key: str, default: Any = None) -> Any:
        """便捷获取上下文数据"""
        return self.mission_data.get(key, default)
    
    def set(self, key: str, value: Any):
        """便捷设置上下文数据"""
        self.mission_data[key] = value


class BehaviorPlugin(ABC):
    """
    行为插件抽象基类
    
    所有行为插件都需要继承此类并实现 execute 方法
    
    使用示例:
        class MyCustomBehavior(BehaviorPlugin):
            def execute(self, context: BehaviorContext) -> bool:
                # 实现自定义行为
                return True
    """
    
    def __init__(self, name: str = None):
        self.name = name or self.__class__.__name__
        self._callbacks: List[Callable[[str, bool], None]] = []
    
    @abstractmethod
    def execute(self, context: BehaviorContext) -> bool:
        """
        执行行为
        
        Args:
            context: 行为执行上下文
            
        Returns:
            bool: 行为是否执行成功
        """
        pass
    
    def on_init(self, context: BehaviorContext):
        """
        行为初始化时的回调（可选实现）
        
        Args:
            context: 行为执行上下文
        """
        pass
    
    def on_cleanup(self, context: BehaviorContext):
        """
        行为清理时的回调（可选实现）
        
        Args:
            context: 行为执行上下文
        """
        pass
    
    def register_callback(self, callback: Callable[[str, bool], None]):
        """
        注册行为完成回调
        
        Args:
            callback: 回调函数，接收 (behavior_name, success) 参数
        """
        self._callbacks.append(callback)
    
    def _notify_callbacks(self, success: bool):
        """通知所有回调"""
        for callback in self._callbacks:
            try:
                callback(self.name, success)
            except Exception:
                pass


class ReturnToBaseBehavior(BehaviorPlugin):
    """
    返回基地行为
    
    使用示例:
        behavior = ReturnToBaseBehavior(
            base_position=PoseStamped(x=0.0, y=0.0),
            on_arrive=on_arrive_callback
        )
    """
    
    def __init__(
        self,
        base_position: Optional[PoseStamped] = None,
        tolerance: float = 0.5,
        on_arrive: Optional[Callable[[], None]] = None,
        navigator: Any = None
    ):
        super().__init__('return_to_base')
        self.base_position = base_position
        self.tolerance = tolerance
        self.on_arrive = on_arrive
        self.navigator = navigator
        self._is_returning = False
        self._return_start_time: Optional[float] = None
    
    def execute(self, context: BehaviorContext) -> bool:
        """执行返回基地行为"""
        try:
            if self.navigator is None:
                context.set('error', 'Navigator not configured')
                return False
            
            if self.base_position is None:
                base_pos = context.get('base_position')
                if base_pos is None:
                    context.set('error', 'Base position not set')
                    return False
                self.base_position = base_pos
            
            self._is_returning = True
            self._return_start_time = time.time()
            
            context.set('returning', True)
            context.set('return_start_time', self._return_start_time)
            
            goal_poses = [self.base_position]
            
            if self.navigator.followWaypoints(goal_poses):
                context.set('return_status', 'navigating')
                return True
            else:
                context.set('error', 'Goal rejected by navigator')
                return False
                
        except Exception as e:
            context.set('error', str(e))
            return False
    
    def check_arrival(self, current_position, current_waypoint: int) -> bool:
        """
        检查是否到达基地
        
        Args:
            current_position: 当前位置 (x, y)
            current_waypoint: 当前航点索引
            
        Returns:
            bool: 是否到达基地
        """
        if not self._is_returning:
            return False
        
        if self.base_position is None:
            return False
        
        dx = current_position[0] - self.base_position.pose.position.x
        dy = current_position[1] - self.base_position.pose.position.y
        distance = (dx * dx + dy * dy) ** 0.5
        
        if distance <= self.tolerance:
            self._is_returning = False
            
            if self.on_arrive:
                try:
                    self.on_arrive()
                except Exception:
                    pass
            
            return True
        
        return False
    
    def is_returning(self) -> bool:
        """是否正在返回"""
        return self._is_returning
    
    def get_return_duration(self) -> float:
        """获取返回持续时间（秒）"""
        if self._return_start_time is None:
            return 0.0
        return time.time() - self._return_start_time


class PauseMissionBehavior(BehaviorPlugin):
    """
    暂停任务行为
    
    使用示例:
        behavior = PauseMissionBehavior(
            timeout=30.0,
            on_pause=on_pause_callback,
            on_resume=on_resume_callback
        )
    """
    
    def __init__(
        self,
        timeout: float = 0.0,
        on_pause: Optional[Callable[[], None]] = None,
        on_resume: Optional[Callable[[], None]] = None
    ):
        super().__init__('pause_mission')
        self.timeout = timeout
        self.on_pause = on_pause
        self.on_resume = on_resume
        self._pause_start_time: Optional[float] = None
        self._is_paused = False
    
    def execute(self, context: BehaviorContext) -> bool:
        """执行暂停行为"""
        try:
            self._is_paused = True
            self._pause_start_time = time.time()
            
            context.set('paused', True)
            context.set('pause_start_time', self._pause_start_time)
            context.set('pause_timeout', self.timeout)
            
            if self.on_pause:
                try:
                    self.on_pause()
                except Exception:
                    pass
            
            return True
            
        except Exception as e:
            context.set('error', str(e))
            return False
    
    def should_resume(self) -> bool:
        """检查是否应该恢复任务"""
        if not self._is_paused:
            return False
        
        if self.timeout <= 0:
            return False
        
        elapsed = time.time() - self._pause_start_time
        return elapsed >= self.timeout
    
    def resume(self, context: BehaviorContext):
        """恢复任务"""
        if not self._is_paused:
            return
        
        self._is_paused = False
        self._pause_start_time = None
        
        context.set('paused', False)
        
        if self.on_resume:
            try:
                self.on_resume()
            except Exception:
                pass
    
    def is_paused(self) -> bool:
        """是否处于暂停状态"""
        return self._is_paused
    
    def get_pause_duration(self) -> float:
        """获取暂停持续时间（秒）"""
        if self._pause_start_time is None:
            return 0.0
        return time.time() - self._pause_start_time


class ContinueMissionBehavior(BehaviorPlugin):
    """
    继续任务行为
    
    用于从中断点恢复任务执行
    
    使用示例:
        behavior = ContinueMissionBehavior(
            on_continue=on_continue_callback
        )
    """
    
    def __init__(
        self,
        on_continue: Optional[Callable[[], None]] = None,
        auto_save_state: bool = True
    ):
        super().__init__('continue_mission')
        self.on_continue = on_continue
        self.auto_save_state = auto_save_state
    
    def execute(self, context: BehaviorContext) -> bool:
        """执行继续任务行为"""
        try:
            if self.auto_save_state:
                context.set('resumed', True)
                context.set('resume_time', time.time())
            
            if self.on_continue:
                try:
                    self.on_continue()
                except Exception:
                    pass
            
            return True
            
        except Exception as e:
            context.set('error', str(e))
            return False


class CompositeBehavior(BehaviorPlugin):
    """
    复合行为 - 按顺序执行多个行为
    
    使用示例:
        composite = CompositeBehavior([
            PauseMissionBehavior(timeout=5.0),
            ReturnToBaseBehavior(base_position),
            ContinueMissionBehavior()
        ])
    """
    
    def __init__(self, behaviors: List[BehaviorPlugin]):
        super().__init__('composite')
        self.behaviors = behaviors
        self._current_index = 0
    
    def execute(self, context: BehaviorContext) -> bool:
        """按顺序执行所有行为"""
        if self._current_index >= len(self.behaviors):
            return True
        
        behavior = self.behaviors[self._current_index]
        success = behavior.execute(context)
        
        if success:
            self._current_index += 1
            return self._current_index >= len(self.behaviors)
        
        return False
    
    def reset(self):
        """重置复合行为"""
        self._current_index = 0
