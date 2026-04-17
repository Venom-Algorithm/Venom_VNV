# venom_bringup

系统启动配置包

## 功能
- 建图模式启动
- 重定位模式启动
- 集成多传感器驱动
- PX4 DDS 探测示例启动

## 启动文件
- `mapping_bringup.launch.py` - 3D+2D 建图
- `relocalization_bringup.launch.py` - 重定位
- `examples/px4_agent_probe.launch.py` - PX4 uXRCE-DDS 连通性探测与桥接状态检查
