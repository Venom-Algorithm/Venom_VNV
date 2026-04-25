---
title: Quick Start
description: The shortest path for a first-time user to clone, build, and verify the
  workspace.
---

## Before You Begin

Make sure the following are already available:

- Ubuntu 22.04
- ROS 2 Humble
- `rosdep`
- `colcon`
- Livox-SDK2

If your base environment is not ready yet, start from [Environment Setup](../deployment/environment.md).

You can verify Livox-SDK2 with:

```bash
ldconfig -p | grep LivoxSdkCore
```

If it is missing, complete [LiDAR Setup](../deployment/lidar_setup.md) first.

If `rosdep install` fails, try:

```bash
sudo rosdep init
rosdep update
```

## Clone the Repository

Recommended first-time clone:

```bash
cd ~
mkdir -p ~/venom_ws/src
git clone --recurse-submodules https://github.com/Venom-Algorithm/Venom_VNV ~/venom_ws/src/venom_vnv
```

If you only need one workflow, clone the main repository first and then initialize a profile-specific submodule set:

```bash
cd ~
mkdir -p ~/venom_ws/src
git clone https://github.com/Venom-Algorithm/Venom_VNV ~/venom_ws/src/venom_vnv
cd ~/venom_ws/src/venom_vnv
make submodules-ugv       # real UGV: chassis, LiDAR, localization, perception
make submodules-sim       # pure simulation: simulation workspace and planning
make submodules-ugv-sim   # UGV simulation: simulation, localization, planning, YOLO
make submodules-auto-aim  # auto-aim development: perception, camera, serial
make submodules-uav       # UAV: PX4 bridge and Ego Planner
make submodules-all       # initialize all submodules
```

For first-time full deployment, `--recurse-submodules` is still the simplest path. For single-area development, the profile targets save time and disk space.

If you want to remove an old workspace and start clean, move back to your home directory first:

Note: if your current shell is still inside `~/venom_ws` or one of its subdirectories, switch back to `~` before removing it. Otherwise the shell may stay attached to an invalid working directory and `git` can fail with `Unable to read current working directory`.

```bash
cd ~
rm -rf ~/venom_ws
mkdir -p ~/venom_ws/src
git clone --recurse-submodules https://github.com/Venom-Algorithm/Venom_VNV ~/venom_ws/src/venom_vnv
```

## Build the Workspace

```bash
cp ~/venom_ws/src/venom_vnv/driver/livox_ros_driver2/package_ROS2.xml \
   ~/venom_ws/src/venom_vnv/driver/livox_ros_driver2/package.xml

cd ~/venom_ws
rosdep install -r --from-paths src --ignore-src --rosdistro $ROS_DISTRO -y
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release -DROS_EDITION=ROS2 -DHUMBLE_ROS=humble
```

After a successful build:

```bash
source ~/venom_ws/install/setup.bash
```

## Update to the Latest Version

If the workspace already exists and you want to sync it to the latest upstream version:

```bash
cd ~/venom_ws/src/venom_vnv
git pull
git submodule sync --recursive
git submodule update --init --recursive
```

If the workspace was initialized with a profile, rerun the matching target after syncing:

```bash
cd ~/venom_ws/src/venom_vnv
git pull
git submodule sync --recursive
make submodules-uav
```

If you also need the recommended Git remote strategy for development machines, see [Development Notes](../support/development.md).

## Suggested Next Steps

1. [Environment Setup](../deployment/environment.md)
2. [LiDAR Setup](../deployment/lidar_setup.md)
3. [Chassis CAN Setup](../deployment/chassis_can_setup.md)
4. [Launch & Use](launch_usage.md)

## First Validation

- LiDAR chain: [Livox LiDAR Driver](../modules/drivers/livox_ros_driver2.md)
- Camera chain: [Hikrobot Camera Driver](../modules/drivers/ros2_hik_camera.md)
- Serial chain: [Serial Driver](../modules/drivers/venom_serial_driver.md)
- System-level interfaces: [Topics & TF Overview](../deployment/system_overview.md)
