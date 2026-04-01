"""
Mission Manager - 任务管理器

提供任务状态机管理和状态持久化功能，支持：
- 任务状态转换（RUNNING, PAUSED, EMERGENCY, COMPLETED）
- 任务状态保存和恢复
- 行为注册和执行
- 多任务并行管理
"""

import rclpy
from rclpy.node import Node
from typing import Any, Callable, Dict, List, Optional, Type
from enum import Enum
from dataclasses import dataclass, field
import threading
import time


class MissionState(Enum):
    """任务状态枚举"""
    IDLE = 'idle'
    RUNNING = 'running'
    PAUSED = 'paused'
    EMERGENCY = 'emergency'
    COMPLETED = 'completed'
    FAILED = 'failed'


@dataclass
class MissionContext:
    """任务上下文"""
    mission_id: str
    state: MissionState = MissionState.IDLE
    data: Dict[str, Any] = field(default_factory=dict)
    created_at: float = 0.0
    updated_at: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StateTransition:
    """状态转换配置"""
    from_state: MissionState
    to_state: MissionState
    condition: Optional[Callable[[], bool]] = None
    on_enter: Optional[Callable[[], None]] = None
    on_exit: Optional[Callable[[], None]] = None


class MissionManager:
    """
    任务管理器
    
    使用示例:
        manager = MissionManager(node)
        
        # 注册行为
        manager.register_behavior(
            MissionState.EMERGENCY,
            emergency_return_behavior
        )
        
        # 保存任务状态
        manager.save_state(
            'navigation',
            {'current_waypoint': 2, 'direction': 'forward'}
        )
        
        # 状态转换
        manager.transition_to(MissionState.EMERGENCY)
        
        # 恢复任务状态
        state = manager.restore_state('navigation')
    """
    
    def __init__(self, node: Node):
        self.node = node
        self._missions: Dict[str, MissionContext] = {}
        self._behaviors: Dict[MissionState, List[Callable]] = {}
        self._transitions: Dict[str, List[StateTransition]] = {}
        self._lock = threading.Lock()
        self._state_history: Dict[str, List[Dict]] = {}
        
        self.node.get_logger().info('MissionManager initialized')
    
    def create_mission(self, mission_id: str, initial_state: MissionState = MissionState.IDLE) -> bool:
        """
        创建新任务
        
        Args:
            mission_id: 任务唯一标识
            initial_state: 初始状态
            
        Returns:
            bool: 是否创建成功
        """
        with self._lock:
            if mission_id in self._missions:
                self.node.get_logger().warning(f'Mission "{mission_id}" already exists')
                return False
            
            current_time = time.time()
            self._missions[mission_id] = MissionContext(
                mission_id=mission_id,
                state=initial_state,
                created_at=current_time,
                updated_at=current_time
            )
            
            self._state_history[mission_id] = []
            self._record_state_change(mission_id, initial_state, 'created')
            
            self.node.get_logger().info(f'Created mission: {mission_id}, state: {initial_state.value}')
            return True
    
    def destroy_mission(self, mission_id: str) -> bool:
        """销毁任务"""
        with self._lock:
            if mission_id not in self._missions:
                return False
            
            del self._missions[mission_id]
            if mission_id in self._state_history:
                del self._state_history[mission_id]
            
            self.node.get_logger().info(f'Destroyed mission: {mission_id}')
            return True
    
    def save_state(self, mission_id: str, state_data: Dict[str, Any]) -> bool:
        """
        保存任务状态数据
        
        Args:
            mission_id: 任务 ID
            state_data: 要保存的状态数据字典
            
        Returns:
            bool: 是否保存成功
        """
        with self._lock:
            if mission_id not in self._missions:
                self.node.get_logger().warning(f'Mission "{mission_id}" not found')
                return False
            
            mission = self._missions[mission_id]
            mission.data.update(state_data)
            mission.updated_at = time.time()
            
            self.node.get_logger().info(
                f'Saved state for mission "{mission_id}": {list(state_data.keys())}'
            )
            return True
    
    def restore_state(self, mission_id: str) -> Optional[Dict[str, Any]]:
        """
        恢复任务状态数据
        
        Args:
            mission_id: 任务 ID
            
        Returns:
            保存的状态数据，如果任务不存在则返回 None
        """
        with self._lock:
            if mission_id not in self._missions:
                self.node.get_logger().warning(f'Mission "{mission_id}" not found')
                return None
            
            mission = self._missions[mission_id]
            self.node.get_logger().info(
                f'Restored state for mission "{mission_id}": {list(mission.data.keys())}'
            )
            return mission.data.copy()
    
    def get_state(self, mission_id: str) -> Optional[MissionState]:
        """获取任务当前状态"""
        with self._lock:
            if mission_id not in self._missions:
                return None
            return self._missions[mission_id].state
    
    def get_mission_data(self, mission_id: str) -> Optional[Dict[str, Any]]:
        """获取任务数据"""
        with self._lock:
            if mission_id not in self._missions:
                return None
            return self._missions[mission_id].data.copy()
    
    def transition_to(
        self,
        mission_id: str,
        new_state: MissionState,
        force: bool = False
    ) -> bool:
        """
        转换任务状态
        
        Args:
            mission_id: 任务 ID
            new_state: 新状态
            force: 是否强制转换（跳过条件检查）
            
        Returns:
            bool: 是否转换成功
        """
        with self._lock:
            if mission_id not in self._missions:
                self.node.get_logger().warning(f'Mission "{mission_id}" not found')
                return False
            
            mission = self._missions[mission_id]
            old_state = mission.state
            
            if old_state == new_state:
                return True
            
            transition_key = f'{old_state.value}->{new_state.value}'
            
            if not force and transition_key in self._transitions:
                for transition in self._transitions[transition_key]:
                    if transition.condition and not transition.condition():
                        self.node.get_logger().warning(
                            f'Transition {transition_key} condition not met'
                        )
                        return False
            
            if transition_key in self._transitions:
                for transition in self._transitions[transition_key]:
                    if transition.on_exit:
                        try:
                            transition.on_exit()
                        except Exception as e:
                            self.node.get_logger().error(f'Error in on_exit callback: {e}')
            
            old_state_value = old_state.value
            mission.state = new_state
            mission.updated_at = time.time()
            
            self._record_state_change(mission_id, new_state, f'transitioned from {old_state_value}')
            
            if transition_key in self._transitions:
                for transition in self._transitions[transition_key]:
                    if transition.on_enter:
                        try:
                            transition.on_enter()
                        except Exception as e:
                            self.node.get_logger().error(f'Error in on_enter callback: {e}')
            
            self.node.get_logger().info(
                f'Mission "{mission_id}" transitioned: {old_state_value} -> {new_state.value}'
            )
            
            self._execute_behaviors(mission_id, new_state)
            
            return True
    
    def register_behavior(
        self,
        state: MissionState,
        behavior: Callable[[str], None],
        priority: int = 0
    ):
        """
        注册状态对应的行为
        
        Args:
            state: 任务状态
            behavior: 行为回调函数，接收 mission_id 参数
            priority: 优先级（数字越大优先级越高）
        """
        if state not in self._behaviors:
            self._behaviors[state] = []
        
        self._behaviors[state].append((priority, behavior))
        self._behaviors[state].sort(key=lambda x: x[0], reverse=True)
        
        self.node.get_logger().info(f'Registered behavior for state: {state.value}')
    
    def register_transition(
        self,
        from_state: MissionState,
        to_state: MissionState,
        condition: Optional[Callable[[], bool]] = None,
        on_enter: Optional[Callable[[], None]] = None,
        on_exit: Optional[Callable[[], None]] = None
    ):
        """注册状态转换规则"""
        key = f'{from_state.value}->{to_state.value}'
        
        if key not in self._transitions:
            self._transitions[key] = []
        
        self._transitions[key].append(StateTransition(
            from_state=from_state,
            to_state=to_state,
            condition=condition,
            on_enter=on_enter,
            on_exit=on_exit
        ))
        
        self.node.get_logger().info(f'Registered transition: {key}')
    
    def is_running(self, mission_id: str) -> bool:
        """检查任务是否正在运行"""
        return self.get_state(mission_id) == MissionState.RUNNING
    
    def is_emergency(self, mission_id: str) -> bool:
        """检查任务是否处于紧急状态"""
        return self.get_state(mission_id) == MissionState.EMERGENCY
    
    def is_completed(self, mission_id: str) -> bool:
        """检查任务是否已完成"""
        return self.get_state(mission_id) == MissionState.COMPLETED
    
    def get_state_history(self, mission_id: str) -> List[Dict]:
        """获取任务状态历史"""
        with self._lock:
            if mission_id not in self._state_history:
                return []
            return self._state_history[mission_id].copy()
    
    def _execute_behaviors(self, mission_id: str, state: MissionState):
        """执行状态对应的行为"""
        if state not in self._behaviors:
            return
        
        for _, behavior in self._behaviors[state]:
            try:
                behavior(mission_id)
            except Exception as e:
                self.node.get_logger().error(
                    f'Error executing behavior for state {state.value}: {e}'
                )
    
    def _record_state_change(self, mission_id: str, state: MissionState, event: str):
        """记录状态变化历史"""
        record = {
            'timestamp': time.time(),
            'state': state.value,
            'event': event
        }
        
        if mission_id not in self._state_history:
            self._state_history[mission_id] = []
        
        self._state_history[mission_id].append(record)
    
    def get_all_missions(self) -> Dict[str, Dict[str, Any]]:
        """获取所有任务的状态信息"""
        with self._lock:
            return {
                mission_id: {
                    'state': mission.state.value,
                    'data': mission.data,
                    'created_at': mission.created_at,
                    'updated_at': mission.updated_at
                }
                for mission_id, mission in self._missions.items()
            }
    
    def clear_all(self):
        """清空所有任务"""
        with self._lock:
            self._missions.clear()
            self._behaviors.clear()
            self._transitions.clear()
            self._state_history.clear()
            self.node.get_logger().info('All missions cleared')
