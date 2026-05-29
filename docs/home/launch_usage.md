---
title: 启动使用
description: 完成编译后的首次启动入口与常用运行命令。
---

## 开始之前

默认你已经完成：

- [快速开始](quick_start.md)
- 需要时完成 [雷达配置](../deployment/lidar_setup.md)
- 需要时完成 [底盘 CAN 部署](../deployment/chassis_can_setup.md)

## 进入工作空间

```bash
cd ~/venom_ws
source install/setup.bash
```

## 常用编译命令

### 1. 标准重新编译

```bash
cp ~/venom_ws/src/venom_vnv/driver/livox_ros_driver2/package_ROS2.xml \
   ~/venom_ws/src/venom_vnv/driver/livox_ros_driver2/package.xml

cd ~/venom_ws
rosdep install -r --from-paths src --ignore-src --rosdistro $ROS_DISTRO -y
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release -DROS_EDITION=ROS2 -DHUMBLE_ROS=humble
```

### 2. 删除 `build` 和 `install` 后重新编译

```bash
cp ~/venom_ws/src/venom_vnv/driver/livox_ros_driver2/package_ROS2.xml \
   ~/venom_ws/src/venom_vnv/driver/livox_ros_driver2/package.xml

cd ~/venom_ws
rm -rf build install
rosdep install -r --from-paths src --ignore-src --rosdistro $ROS_DISTRO -y
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release -DROS_EDITION=ROS2 -DHUMBLE_ROS=humble
```

## 更新到最新版本

如果你已经在另一台机器上拉过仓库，后续想把主仓库和全部子模块一起更新到当前最新版本，可以执行：

```bash
cd ~/venom_ws/src/venom_vnv
git pull origin master
git submodule sync --recursive
git submodule update --init --recursive
```

## 常用启动命令

### 1. Mid360 RViz 验证

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch venom_bringup mid360_rviz.launch.py
```

### 2. Mid360 + Point-LIO

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch venom_bringup mid360_point_lio.launch.py
```

### 3. Mid360 + Point-LIO 纯里程计模式

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch venom_bringup mid360_point_lio_odom.launch.py
```

这个入口默认使用 `point_lio_online_odom.yaml`，适合只需要高实时性 `odom -> base_link`、不需要地图发布和 PCD 保存的场景。

### 4. Mid360 + Point-LIO 显式异步地图模式

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch venom_bringup mid360_point_lio_async_map.launch.py
```

### 5. Point-LIO 离线导图

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch venom_bringup mid360_point_lio_offline_map.launch.py \
  bag_path:=/absolute/path/to/rosbag2_dir \
  output_pcd_path:=/absolute/path/to/offline_map.pcd
```

### 6. D435i / RealSense 验证

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch venom_bringup d435i_test.launch.py
```

### 7. PX4 VPS / 外部位姿桥接

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch venom_bringup px4_vps_bridge.launch.py
```

如果 LIO 或 VPS 输出话题不是默认的 `/lio/vps/odometry`：

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch venom_bringup px4_vps_bridge.launch.py input_odom_topic:=/lio/odom
```

### 8. 带健康状态监听的多航点导航

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch venom_bringup health_aware_navigation.launch.py
```

如果只想直接运行 Nav2 Simple Commander 多航点入口：

```bash
cd ~/venom_ws
source install/setup.bash
ros2 run venom_bringup multi_waypoint_commander
```

### 关于 `robot_bringup.launch.py`

`robot_bringup.launch.py` 当前已经保留顶层 `robot_type` 选择逻辑，但它依赖各机器人子目录下的整机模板 launch。当前日常联调请优先使用本页列出的具体 launch 文件。

## 建议阅读顺序

如果你只是第一次联调，建议按这个顺序来：

1. 先跑 Mid360 RViz 验证
2. 再跑 Mid360 + Point-LIO
3. 如果只需要高实时 odom，可以改跑 Mid360 + Point-LIO 纯里程计模式
4. 如果要显式测试异步地图缓存，可以跑 Mid360 + Point-LIO 异步地图模式
5. 如果要离线导图，使用 Point-LIO 离线导图入口并指定 rosbag2
6. 如果要接 RealSense，再跑 D435i / RealSense 验证
7. 如果要把外部定位喂给 PX4，再跑 PX4 VPS / 外部位姿桥接
8. 如果要验证任务控制，再跑健康状态监听的多航点导航

## 进一步阅读

- 启动入口设计：参考 [系统层](../modules/integration/index.md)
- 不同模式说明：参考 [运行模式](../deployment/run_modes.md)
