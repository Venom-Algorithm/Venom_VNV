"""
Plugins Package - 插件系统

提供通用框架下的具体实现插件：
- HealthPlugin: 血量监控插件
- NavigationPlugin: 导航任务插件

使用示例:
    from plugins import HealthPlugin, NavigationPlugin
"""

from .health_plugin import HealthPlugin
from .navigation_plugin import NavigationPlugin

__all__ = [
    'HealthPlugin',
    'NavigationPlugin',
]
