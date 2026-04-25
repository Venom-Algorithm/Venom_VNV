---
title: RealSense Setup
description: Install librealsense, the ROS 2 wrapper, and validate D435 / D435i in
  this repository.
---

## Scope

This page is for Intel RealSense D435 / D435i deployment on Ubuntu 22.04 + ROS 2 Humble, including the repository-side `d435i_test.launch.py` validation flow.

Official references:

- [librealsense Linux manual installation guide](https://github.com/realsenseai/librealsense/blob/master/doc/distribution_linux.md#installing-the-packages)
- [realsense-ros repository](https://github.com/realsenseai/realsense-ros)

## Register the APT Key

```bash
sudo mkdir -p /etc/apt/keyrings

curl -sSf https://librealsense.realsenseai.com/Debian/librealsenseai.asc | \
gpg --dearmor | sudo tee /etc/apt/keyrings/librealsenseai.gpg > /dev/null
```

## Install APT HTTPS Support

```bash
sudo apt-get update
sudo apt-get install -y apt-transport-https
```

## Add the RealSense Repository

```bash
echo "deb [signed-by=/etc/apt/keyrings/librealsenseai.gpg] https://librealsense.realsenseai.com/Debian/apt-repo `lsb_release -cs` main" | \
sudo tee /etc/apt/sources.list.d/librealsense.list

sudo apt-get update
```

## Install Runtime Packages

```bash
sudo apt-get install -y librealsense2-dkms
sudo apt-get install -y librealsense2-utils
```

These packages install udev rules, kernel modules, runtime libraries, and tools such as `realsense-viewer`.

## Optional Development Packages

```bash
sudo apt-get install -y librealsense2-dev
sudo apt-get install -y librealsense2-dbg
```

## Install the ROS 2 Wrapper

This repository uses `realsense2_camera` from the ROS wrapper, so install it as well:

```bash
sudo apt update
sudo apt install -y ros-$ROS_DISTRO-realsense2-*
```

On Humble, the equivalent explicit form is:

```bash
sudo apt update
sudo apt install -y ros-humble-realsense2-*
```

## Basic Validation

Reconnect the camera, then run:

```bash
realsense-viewer
```

Then verify the kernel module:

```bash
modinfo uvcvideo | grep "version:"
```

The output should include the `realsense` string.

## Repository-Side Validation

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch venom_bringup d435i_test.launch.py
```

This launch currently uses:

- namespace: `camera`
- camera name: `d435i`
- depth profile: `640x480x30`
- color, depth, gyro, accel enabled
- point cloud enabled
- RViz enabled by default

## Common Checks

- `realsense-viewer: command not found`
  `librealsense2-utils` is usually missing.

- `Package 'realsense2_camera' not found`
  The ROS 2 wrapper has not been installed yet.

- `modinfo uvcvideo` does not include `realsense`
  `librealsense2-dkms` likely did not activate correctly. Reinstall it, reconnect the camera, and reboot if needed.

## Related Pages

- [Environment Setup](environment.md)
- [Launch & Use](../home/launch_usage.md)
