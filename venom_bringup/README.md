# venom_bringup

系统启动配置包

## 功能
- 建图模式启动
- 重定位模式启动
- 集成多传感器驱动
- PX4 DDS 探测示例启动
- PX4 外部位姿桥接
- 当前过渡阶段的多航点任务控制入口

## 启动文件
- `mid360_rviz.launch.py` - Mid360 + RViz 验证
- `mid360_point_lio.launch.py` - Mid360 + Point-LIO 联调
- `mid360_point_lio_odom.launch.py` - Mid360 + Point-LIO 纯里程计模式
- `mid360_point_lio_async_map.launch.py` - Mid360 + Point-LIO 异步地图模式
- `mid360_point_lio_offline_map.launch.py` - Point-LIO 离线导图
- `d435i_test.launch.py` - RealSense D435i 验证
- `scout_mini_mapping.launch.py` - Scout Mini 3D+2D 建图
- `sentry_mapping.launch.py` - Sentry 3D+2D 建图
- `relocalization_bringup.launch.py` - 重定位
- `px4_agent_probe.launch.py` - PX4 uXRCE-DDS 连通性探测与桥接状态检查
- `px4_vps_bridge.launch.py` - PX4 外部位姿桥接
- `health_aware_navigation.launch.py` - 带状态监听和恢复逻辑的多航点导航

源码中部分 launch 位于 `launch/examples/`、`launch/sentry/`、`launch/scout_mini/` 等子目录；使用 `ros2 launch` 时直接写 launch 文件名即可。

```bash
ros2 launch venom_bringup mid360_rviz.launch.py
ros2 launch venom_bringup health_aware_navigation.launch.py
```

## 任务控制代码

当前任务控制框架仍在本包内维护：

- `venom_bringup/multi_waypoint_commander.py`
- `venom_bringup/health_aware_commander.py`
- `venom_bringup/mission_controller/`
- `venom_bringup/plugins/`
- `config/scout_mini/mission_config.yaml`
- `config/scout_mini/waypoints.yaml`

后续新增独立任务包时，应优先放入主仓库的 `mission/` 层。
