# venom_bringup

系统启动配置包

## 功能
- 建图模式启动
- 重定位模式启动
- 集成多传感器驱动
- PX4 DDS 探测示例启动

## 启动文件
- `scout_mini_mapping.launch.py` - Scout Mini 3D+2D 建图
- `sentry_mapping.launch.py` - Sentry 3D+2D 建图
- `relocalization_bringup.launch.py` - 重定位
- `px4_agent_probe.launch.py` - PX4 uXRCE-DDS 连通性探测与桥接状态检查
- `px4_vps_bridge.launch.py` - PX4 外部位姿桥接
