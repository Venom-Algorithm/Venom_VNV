---
title: Quick Start
permalink: /en/quick_start
desc: The shortest path for a first-time user to clone, build, and verify the workspace.
breadcrumb: Deployment & Usage
layout: default
---

## Before You Begin

Make sure the following are already available:

- Ubuntu 22.04
- ROS 2 Humble
- `rosdep`
- `colcon`
- Livox-SDK2

If your base environment is not ready yet, start from [Environment Setup]({{ '/en/environment' | relative_url }}).

You can verify Livox-SDK2 with:

```bash
ldconfig -p | grep LivoxSdkCore
```

If it is missing, complete [LiDAR Setup]({{ '/en/lidar_setup' | relative_url }}) first.

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

If you also need the recommended Git remote strategy for development machines, see [Development Notes]({{ '/en/development' | relative_url }}).

## Suggested Next Steps

1. [Environment Setup]({{ '/en/environment' | relative_url }})
2. [LiDAR Setup]({{ '/en/lidar_setup' | relative_url }})
3. [Chassis CAN Setup]({{ '/en/chassis_can_setup' | relative_url }})
4. [Launch & Use]({{ '/en/launch_usage' | relative_url }})

## First Validation

- LiDAR chain: [Livox LiDAR Driver]({{ '/en/livox_ros_driver2' | relative_url }})
- Camera chain: [Hikrobot Camera Driver]({{ '/en/ros2_hik_camera' | relative_url }})
- Serial chain: [Serial Driver]({{ '/en/venom_serial_driver' | relative_url }})
- System-level interfaces: [Topics & TF Overview]({{ '/en/system_overview' | relative_url }})
