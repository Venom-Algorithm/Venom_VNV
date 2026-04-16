---
title: 启动使用
permalink: /launch_usage
desc: 完成编译后的首次启动入口与常用运行命令。
breadcrumb: 首页
layout: default
---

## 开始之前

默认你已经完成：

- [快速开始]({{ '/quick_start' | relative_url }})
- 需要时完成 [雷达配置]({{ '/lidar_setup' | relative_url }})
- 需要时完成 [底盘 CAN 部署]({{ '/chassis_can_setup' | relative_url }})

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
ros2 launch venom_bringup examples/mid360_rviz.launch.py
```

### 2. Mid360 + Point-LIO

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch venom_bringup examples/mid360_point_lio.launch.py
```

### 3. 相机链路验证

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch venom_bringup camera.launch.py
```

### 4. 步兵自瞄

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch venom_bringup infantry/infantry_auto_aim.launch.py
```

### 5. Scout Mini 建图

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch venom_bringup scout_mini/scout_mini_mapping.launch.py
```

### 6. 哨兵建图

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch venom_bringup sentry/sentry_mapping.launch.py
```

### 7. 重定位

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch venom_bringup relocalization_bringup.launch.py
```

### 8. 整机入口

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch venom_bringup robot_bringup.launch.py
```

## 建议阅读顺序

如果你只是第一次联调，建议按这个顺序来：

1. 先跑 Mid360 RViz 验证
2. 再跑 Mid360 + Point-LIO
3. 再按任务需求选择相机、自瞄、建图或重定位
4. 最后再进入整机入口

## 进一步阅读

- 启动入口设计：参考 [系统集成]({{ '/integration_overview' | relative_url }})
- 不同模式说明：参考 [运行模式]({{ '/run_modes' | relative_url }})
