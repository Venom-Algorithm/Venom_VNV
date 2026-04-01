"""
Navigation Plugin - 导航任务插件

提供导航任务的管理功能：
- 航点任务执行
- 往返巡航
- 任务状态保存和恢复
- 与血量插件配合实现紧急返回

使用示例:
    nav_plugin = NavigationPlugin(navigator, state_monitor, mission_manager)
    nav_plugin.load_waypoints(waypoints_file)
    nav_plugin.start_mission(loop=True)
"""

from typing import Any, Dict, List, Optional, Tuple
from geometry_msgs.msg import PoseStamped
import math
import os
import yaml

from mission_controller.mission_manager import MissionManager, MissionState
from mission_controller.behavior_plugins import BehaviorContext


class NavigationPlugin:
    """
    导航任务插件
    
    功能:
    - 加载和管理航点
    - 执行往返巡航任务
    - 保存和恢复导航状态
    - 支持循环任务
    """
    
    def __init__(
        self,
        navigator: Any,
        mission_manager: MissionManager,
        mission_id: str = 'navigation'
    ):
        """
        初始化导航插件
        
        Args:
            navigator: 导航器实例（BasicNavigator 或类似）
            mission_manager: 任务管理器实例
            mission_id: 任务 ID
        """
        self.navigator = navigator
        self.mission_manager = mission_manager
        self.mission_id = mission_id
        
        self._waypoints: List[Dict[str, Any]] = []
        self._goal_poses: List[PoseStamped] = []
        
        self._current_index: int = 0
        self._total_waypoints: int = 0
        self._direction: str = 'forward'
        self._loop: bool = False
        self._is_mission_active: bool = False
        
        self._mission_complete_callback: Optional[callable] = None
        
        if hasattr(navigator, 'get_logger'):
            self.navigator.get_logger().info('NavigationPlugin initialized')
    
    def load_waypoints_from_file(self, file_path: str) -> bool:
        """
        从 YAML 文件加载航点
        
        Args:
            file_path: YAML 文件路径
            
        Returns:
            bool: 是否加载成功
        """
        try:
            if not os.path.isfile(file_path):
                if hasattr(self.navigator, 'get_logger'):
                    self.navigator.get_logger().error(f'Waypoints file not found: {file_path}')
                return False
            
            with open(file_path, 'r') as f:
                data = yaml.safe_load(f)
            
            if 'waypoints' not in data:
                if hasattr(self.navigator, 'get_logger'):
                    self.navigator.get_logger().error('No waypoints found in YAML file')
                return False
            
            self._waypoints = data['waypoints']
            self._total_waypoints = len(self._waypoints)
            self._goal_poses = self._waypoints_to_poses(self._waypoints)
            
            if hasattr(self.navigator, 'get_logger'):
                self.navigator.get_logger().info(
                    f'Loaded {self._total_waypoints} waypoints from {file_path}'
                )
            
            return True
            
        except Exception as e:
            if hasattr(self.navigator, 'get_logger'):
                self.navigator.get_logger().error(f'Error loading waypoints: {e}')
            return False
    
    def load_waypoints(self, waypoints: List[Dict[str, Any]]) -> bool:
        """
        直接从列表加载航点
        
        Args:
            waypoints: 航点列表，每个元素包含 frame_id, x, y, yaw
            
        Returns:
            bool: 是否加载成功
        """
        try:
            self._waypoints = waypoints
            self._total_waypoints = len(waypoints)
            self._goal_poses = self._waypoints_to_poses(waypoints)
            
            if hasattr(self.navigator, 'get_logger'):
                self.navigator.get_logger().info(
                    f'Loaded {self._total_waypoints} waypoints'
                )
            
            return True
            
        except Exception as e:
            if hasattr(self.navigator, 'get_logger'):
                self.navigator.get_logger().error(f'Error loading waypoints: {e}')
            return False
    
    def _waypoints_to_poses(self, waypoints: List[Dict]) -> List[PoseStamped]:
        """将航点列表转换为 PoseStamped 列表"""
        poses = []
        
        for wp in waypoints:
            pose = PoseStamped()
            pose.header.frame_id = wp.get('frame_id', 'map')
            pose.header.stamp = self.navigator.get_clock().now().to_msg()
            
            pose.pose.position.x = float(wp['x'])
            pose.pose.position.y = float(wp['y'])
            pose.pose.position.z = 0.0
            
            yaw = float(wp.get('yaw', 0.0))
            pose.pose.orientation.x = 0.0
            pose.pose.orientation.y = 0.0
            pose.pose.orientation.z = math.sin(yaw / 2.0)
            pose.pose.orientation.w = math.cos(yaw / 2.0)
            
            poses.append(pose)
        
        return poses
    
    def start_mission(
        self,
        loop: bool = False,
        start_index: int = 0,
        direction: str = 'forward'
    ) -> bool:
        """
        开始导航任务
        
        Args:
            loop: 是否循环执行
            start_index: 起始航点索引
            direction: 初始方向（forward/return）
            
        Returns:
            bool: 是否启动成功
        """
        if not self._waypoints:
            if hasattr(self.navigator, 'get_logger'):
                self.navigator.get_logger().error('No waypoints loaded')
            return False
        
        self._loop = loop
        self._current_index = start_index
        self._direction = direction
        self._is_mission_active = True
        
        self.mission_manager.create_mission(self.mission_id, MissionState.RUNNING)
        
        if hasattr(self.navigator, 'get_logger'):
            self.navigator.get_logger().info(
                f'Starting mission: {self._total_waypoints} waypoints, '
                f'loop={loop}, start={start_index}, direction={direction}'
            )
        
        return self._navigate_to_current_waypoint()
    
    def _navigate_to_current_waypoint(self) -> bool:
        """导航到当前航点"""
        if self._current_index >= len(self._goal_poses):
            self._on_mission_complete()
            return False
        
        goal_pose = [self._goal_poses[self._current_index]]
        
        if hasattr(self.navigator, 'get_logger'):
            wp = self._waypoints[self._current_index]
            self.navigator.get_logger().info(
                f'Navigating to waypoint {self._current_index + 1}/{self._total_waypoints} '
                f'(x={wp["x"]:.2f}, y={wp["y"]:.2f})'
            )
        
        accepted = self.navigator.followWaypoints(goal_pose)
        
        if not accepted:
            if hasattr(self.navigator, 'get_logger'):
                self.navigator.get_logger().error('Goal rejected by navigator')
            return False
        
        return True
    
    def update(self) -> Tuple[bool, bool]:
        """
        更新任务状态（需要在主循环中调用）
        
        Returns:
            (is_complete, should_continue) 元组
        """
        if not self._is_mission_active:
            return False, False
        
        if self.navigator.isTaskComplete():
            return self._on_waypoint_reached()
        
        return False, True
    
    def _on_waypoint_reached(self) -> Tuple[bool, bool]:
        """到达航点后的处理"""
        self._current_index += 1
        
        if self._direction == 'forward' and self._current_index >= self._total_waypoints:
            if self._loop:
                self._direction = 'return'
                self._current_index = self._total_waypoints - 2
                if self._current_index < 0:
                    self._current_index = 0
            else:
                self._on_mission_complete()
                return True, False
        
        elif self._direction == 'return' and self._current_index < 0:
            if self._loop:
                self._direction = 'forward'
                self._current_index = 1
                if self._current_index >= self._total_waypoints:
                    self._current_index = 0
            else:
                self._on_mission_complete()
                return True, False
        
        self._save_current_state()
        
        return False, self._navigate_to_current_waypoint()
    
    def _on_mission_complete(self):
        """任务完成处理"""
        self._is_mission_active = False
        self.mission_manager.transition_to(
            self.mission_id,
            MissionState.COMPLETED
        )
        
        if hasattr(self.navigator, 'get_logger'):
            self.navigator.get_logger().info('Mission complete!')
        
        if self._mission_complete_callback:
            try:
                self._mission_complete_callback()
            except Exception as e:
                if hasattr(self.navigator, 'get_logger'):
                    self.navigator.get_logger().error(f'Error in complete callback: {e}')
    
    def _save_current_state(self):
        """保存当前导航状态"""
        state_data = {
            'current_waypoint': self._current_index,
            'total_waypoints': self._total_waypoints,
            'direction': self._direction,
            'loop': self._loop,
            'waypoint_data': self._waypoints[self._current_index] if self._current_index < len(self._waypoints) else None
        }
        
        self.mission_manager.save_state(self.mission_id, state_data)
    
    def restore_state(self) -> Optional[Dict[str, Any]]:
        """恢复导航状态"""
        state_data = self.mission_manager.restore_state(self.mission_id)
        
        if state_data is None:
            return None
        
        self._current_index = state_data.get('current_waypoint', 0)
        self._total_waypoints = state_data.get('total_waypoints', 0)
        self._direction = state_data.get('direction', 'forward')
        self._loop = state_data.get('loop', False)
        
        return state_data
    
    def set_mission_complete_callback(self, callback: callable):
        """设置任务完成回调"""
        self._mission_complete_callback = callback
    
    def get_current_waypoint(self) -> int:
        """获取当前航点索引"""
        return self._current_index
    
    def get_total_waypoints(self) -> int:
        """获取总航点数"""
        return self._total_waypoints
    
    def get_direction(self) -> str:
        """获取当前方向"""
        return self._direction
    
    def is_mission_active(self) -> bool:
        """任务是否正在进行"""
        return self._is_mission_active
    
    def is_mission_complete(self) -> bool:
        """任务是否已完成"""
        return self.mission_manager.is_completed(self.mission_id)
    
    def get_progress(self) -> float:
        """获取任务进度（0.0-1.0）"""
        if self._total_waypoints == 0:
            return 0.0
        return self._current_index / self._total_waypoints
    
    def get_status(self) -> Dict[str, Any]:
        """获取任务状态信息"""
        return {
            'active': self._is_mission_active,
            'current_waypoint': self._current_index,
            'total_waypoints': self._total_waypoints,
            'direction': self._direction,
            'loop': self._loop,
            'progress': self.get_progress(),
            'mission_state': self.mission_manager.get_state(self.mission_id).value if self.mission_manager.get_state(self.mission_id) else 'unknown'
        }
    
    def cancel_mission(self):
        """取消任务"""
        self._is_mission_active = False
        self.mission_manager.transition_to(
            self.mission_id,
            MissionState.IDLE
        )
        
        if hasattr(self.navigator, 'get_logger'):
            self.navigator.get_logger().info('Mission cancelled')
