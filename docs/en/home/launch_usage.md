---
title: Launch & Use
permalink: /en/launch_usage
desc: Common build, rebuild, and launch commands after the workspace has been compiled.
breadcrumb: Home
layout: default
---

## Before You Begin

This page assumes you already completed:

- [Quick Start]({{ '/en/quick_start' | relative_url }})
- [LiDAR Setup]({{ '/en/lidar_setup' | relative_url }}) when needed
- [Chassis CAN Setup]({{ '/en/chassis_can_setup' | relative_url }}) when needed

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

### 3. D435i / RealSense validation

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch venom_bringup d435i_test.launch.py
```

### 4. PX4 VPS / external-pose bridge

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

## Suggested Order

1. Validate Mid360 in RViz
2. Bring up Mid360 + Point-LIO
3. If you use a RealSense camera, validate D435i / RealSense next
4. If external localization is fed into PX4, run the PX4 VPS / external-pose bridge

## Further Reading

- [System Bringup]({{ '/en/venom_bringup' | relative_url }})
- [Run Modes]({{ '/en/run_modes' | relative_url }})
