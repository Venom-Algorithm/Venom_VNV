---
title: Launch & Use
description: Common build, rebuild, and launch commands after the workspace has been
  compiled.
---

## Before You Begin

This page assumes you already completed:

- [Quick Start](quick_start.md)
- [LiDAR Setup](../deployment/lidar_setup.md) when needed
- [Chassis CAN Setup](../deployment/chassis_can_setup.md) when needed

## Enter the Workspace

```bash
cd ~/venom_ws
source install/setup.bash
```

## Common Build Commands

### 1. Standard rebuild

```bash
cp ~/venom_ws/src/venom_vnv/driver/livox_ros_driver2/package_ROS2.xml \
   ~/venom_ws/src/venom_vnv/driver/livox_ros_driver2/package.xml

cd ~/venom_ws
rosdep install -r --from-paths src --ignore-src --rosdistro $ROS_DISTRO -y
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release -DROS_EDITION=ROS2 -DHUMBLE_ROS=humble
```

### 2. Clean `build` and `install`, then rebuild

```bash
cp ~/venom_ws/src/venom_vnv/driver/livox_ros_driver2/package_ROS2.xml \
   ~/venom_ws/src/venom_vnv/driver/livox_ros_driver2/package.xml

cd ~/venom_ws
rm -rf build install
rosdep install -r --from-paths src --ignore-src --rosdistro $ROS_DISTRO -y
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release -DROS_EDITION=ROS2 -DHUMBLE_ROS=humble
```

## Update to the Latest Upstream Version

```bash
cd ~/venom_ws/src/venom_vnv
git pull origin master
git submodule sync --recursive
git submodule update --init --recursive
```

## Common Launch Commands

### 1. Mid360 RViz validation

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

### 3. Mid360 + Point-LIO odom-only mode

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch venom_bringup mid360_point_lio_odom.launch.py
```

This entry uses `point_lio_online_odom.yaml` by default. Use it when you only need realtime `odom -> base_link` output and do not need map publication or PCD saving.

### 4. Mid360 + Point-LIO explicit async-map mode

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch venom_bringup mid360_point_lio_async_map.launch.py
```

### 5. Point-LIO offline mapping

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch venom_bringup mid360_point_lio_offline_map.launch.py \
  bag_path:=/absolute/path/to/rosbag2_dir \
  output_pcd_path:=/absolute/path/to/offline_map.pcd
```

### 6. D435i / RealSense validation

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch venom_bringup d435i_test.launch.py
```

### 7. PX4 VPS / external-pose bridge

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch venom_bringup px4_vps_bridge.launch.py
```

If the LIO or VPS output topic is not the default `/lio/vps/odometry`:

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch venom_bringup px4_vps_bridge.launch.py input_odom_topic:=/lio/odom
```

### 8. Health-aware multi-waypoint navigation

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch venom_bringup health_aware_navigation.launch.py
```

If you only need the Nav2 Simple Commander waypoint entry:

```bash
cd ~/venom_ws
source install/setup.bash
ros2 run venom_bringup multi_waypoint_commander
```

### About `robot_bringup.launch.py`

`robot_bringup.launch.py` already contains top-level `robot_type` selection logic, but it depends on per-robot bringup templates under each robot directory. For daily integration, use the concrete launch files listed on this page first.

## Suggested Order

1. Validate Mid360 in RViz
2. Bring up Mid360 + Point-LIO
3. If you only need realtime odometry, use the Mid360 + Point-LIO odom-only mode
4. If you need to explicitly test async-map buffering, run the Mid360 + Point-LIO async-map mode
5. If offline mapping is needed, use the Point-LIO offline mapping entry with a rosbag2 path
6. If you use a RealSense camera, validate D435i / RealSense next
7. If external localization is fed into PX4, run the PX4 VPS / external-pose bridge
8. If mission control is needed, run the health-aware waypoint navigation entry

## Further Reading

- [System Bringup](../modules/integration/venom_bringup.md)
- [Run Modes](../deployment/run_modes.md)
