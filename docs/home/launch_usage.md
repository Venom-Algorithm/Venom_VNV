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

### 3. D435i / RealSense 验证

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch venom_bringup d435i_test.launch.py
```

### 4. PX4 VPS / 外部位姿桥接

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

## 建议阅读顺序

如果你只是第一次联调，建议按这个顺序来：

1. 先跑 Mid360 RViz 验证
2. 再跑 Mid360 + Point-LIO
3. 如果要接 RealSense，再跑 D435i / RealSense 验证
4. 如果要把外部定位喂给 PX4，再跑 PX4 VPS / 外部位姿桥接

## 进一步阅读

- 启动入口设计：参考 [系统层](../modules/integration/index.md)
- 不同模式说明：参考 [运行模式](../deployment/run_modes.md)
