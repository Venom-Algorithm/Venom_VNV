"""
State Monitor - 通用状态监控器

提供对任意 ROS 话题的订阅和条件判断功能，支持：
- 多话题订阅
- 多种条件判断（阈值、范围、自定义函数）
- 动态添加/移除监控器
- 触发回调机制
"""

import rclpy
from rclpy.node import Node
from typing import Any, Callable, Dict, List, Optional, Type, Union
from dataclasses import dataclass, field
import threading


@dataclass
class MonitorConfig:
    """监控器配置"""
    name: str
    topic: str
    msg_type: Type
    field: str
    condition: Callable[[Any], bool]
    on_trigger: Callable[[Any], None]
    last_value: Any = None
    last_triggered: float = 0.0
    trigger_count: int = 0
    enabled: bool = True
    cooldown: float = 0.0  # 触发冷却时间（秒）


@dataclass
class MonitorResult:
    """监控结果"""
    name: str
    value: Any
    triggered: bool
    timestamp: float


class StateMonitor(Node):
    """
    通用状态监控器
    
    使用示例:
        monitor = StateMonitor()
        
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
    """
    
    def __init__(self, node_name: str = 'state_monitor', **kwargs):
        super().__init__(node_name, **kwargs)
        self._monitors: Dict[str, MonitorConfig] = {}
        self._subscribers: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self._latest_values: Dict[str, Any] = {}
        
    def add_monitor(
        self,
        name: str,
        topic: str,
        msg_type: Type,
        field: str,
        condition: Callable[[Any], bool],
        on_trigger: Callable[[Any], None],
        cooldown: float = 0.0
    ) -> bool:
        """
        添加监控条件
        
        Args:
            name: 监控器名称（唯一标识）
            topic: 订阅的话题名称
            msg_type: ROS 消息类型
            field: 监控的字段名（支持嵌套，如 "battery.percentage"）
            condition: 条件判断函数，接收字段值，返回 bool
            on_trigger: 触发时的回调函数，接收字段值
            cooldown: 触发冷却时间（秒），避免频繁触发
            
        Returns:
            bool: 是否添加成功
        """
        with self._lock:
            if name in self._monitors:
                self.get_logger().warning(f'Monitor "{name}" already exists, updating...')
                self._remove_monitor_unsafe(name)
            
            config = MonitorConfig(
                name=name,
                topic=topic,
                msg_type=msg_type,
                field=field,
                condition=condition,
                on_trigger=on_trigger,
                cooldown=cooldown
            )
            
            self._monitors[name] = config
            
            if topic not in self._subscribers:
                self._create_subscriber(topic, msg_type)
            
            self.get_logger().info(f'Added monitor: {name} on topic {topic}, field: {field}')
            return True
    
    def remove_monitor(self, name: str) -> bool:
        """
        移除监控条件
        
        Args:
            name: 监控器名称
            
        Returns:
            bool: 是否移除成功
        """
        with self._lock:
            return self._remove_monitor_unsafe(name)
    
    def _remove_monitor_unsafe(self, name: str) -> bool:
        """内部移除方法（需要在锁内调用）"""
        if name not in self._monitors:
            self.get_logger().warning(f'Monitor "{name}" not found')
            return False
        
        del self._monitors[name]
        self.get_logger().info(f'Removed monitor: {name}')
        return True
    
    def enable_monitor(self, name: str) -> bool:
        """启用监控器"""
        with self._lock:
            if name in self._monitors:
                self._monitors[name].enabled = True
                self.get_logger().info(f'Enabled monitor: {name}')
                return True
            return False
    
    def disable_monitor(self, name: str) -> bool:
        """禁用监控器"""
        with self._lock:
            if name in self._monitors:
                self._monitors[name].enabled = False
                self.get_logger().info(f'Disabled monitor: {name}')
                return True
            return False
    
    def get_monitor_value(self, name: str) -> Optional[Any]:
        """
        获取监控器的当前值
        
        Args:
            name: 监控器名称
            
        Returns:
            当前值，如果监控器不存在则返回 None
        """
        with self._lock:
            if name in self._monitors:
                return self._monitors[name].last_value
            return None
    
    def get_all_values(self) -> Dict[str, Any]:
        """获取所有监控器的当前值"""
        with self._lock:
            return {
                name: config.last_value
                for name, config in self._monitors.items()
                if config.last_value is not None
            }
    
    def get_monitor_status(self, name: str) -> Optional[Dict[str, Any]]:
        """
        获取监控器状态信息
        
        Returns:
            包含监控器状态的字典，如果不存在则返回 None
        """
        with self._lock:
            if name not in self._monitors:
                return None
            
            config = self._monitors[name]
            return {
                'name': config.name,
                'topic': config.topic,
                'field': config.field,
                'enabled': config.enabled,
                'last_value': config.last_value,
                'trigger_count': config.trigger_count,
                'last_triggered': config.last_triggered
            }
    
    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有监控器的状态"""
        with self._lock:
            return {
                name: self.get_monitor_status(name)
                for name in self._monitors
            }
    
    def _create_subscriber(self, topic: str, msg_type: Type):
        """创建话题订阅者"""
        def callback(msg):
            self._process_message(topic, msg)
        
        self._subscribers[topic] = self.create_subscription(
            msg_type,
            topic,
            callback,
            10
        )
        self.get_logger().debug(f'Created subscriber for topic: {topic}')
    
    def _process_message(self, topic: str, msg):
        """处理接收到的消息"""
        with self._lock:
            current_time = self.get_clock().now().seconds_nanoseconds()[0]
            
            for name, config in list(self._monitors.items()):
                if config.topic != topic or not config.enabled:
                    continue
                
                value = self._get_field_value(msg, config.field)
                config.last_value = value
                
                if value is None:
                    continue
                
                if config.condition(value):
                    config.trigger_count += 1
                    
                    if config.cooldown > 0:
                        time_since_last = current_time - config.last_triggered
                        if time_since_last < config.cooldown:
                            continue
                    
                    config.last_triggered = current_time
                    
                    self.get_logger().info(
                        f'Monitor "{name}" triggered: {config.field} = {value}'
                    )
                    
                    try:
                        config.on_trigger(value)
                    except Exception as e:
                        self.get_logger().error(
                            f'Error in trigger callback for "{name}": {e}'
                        )
    
    def _get_field_value(self, msg, field_path: str) -> Any:
        """
        从消息中获取字段值（支持嵌套字段）
        
        Args:
            msg: ROS 消息对象
            field_path: 字段路径，如 "hp_percentage" 或 "battery.percentage"
            
        Returns:
            字段值，如果字段不存在则返回 None
        """
        try:
            fields = field_path.split('.')
            value = msg
            
            for field in fields:
                if hasattr(value, field):
                    value = getattr(value, field)
                elif isinstance(value, dict) and field in value:
                    value = value[field]
                else:
                    self.get_logger().warning(
                        f'Field "{field}" not found in message'
                    )
                    return None
            
            return value
        except Exception as e:
            self.get_logger().error(f'Error getting field "{field_path}": {e}')
            return None
    
    def destroy(self):
        """销毁监控器"""
        for sub in self._subscribers.values():
            self.destroy_subscription(sub)
        self._monitors.clear()
        self._subscribers.clear()
        self.get_logger().info('StateMonitor destroyed')
