---
title: LiDAR Setup
permalink: /en/lidar_setup
desc: Install Livox-SDK2, configure MID360 networking, and validate the LiDAR chain.
breadcrumb: Deployment & Usage
layout: default
---

## Install Livox-SDK2

```bash
cd ~
sudo apt update
sudo apt install -y cmake git
git clone https://github.com/Livox-SDK/Livox-SDK2.git
cd Livox-SDK2
mkdir -p build
cd build
cmake ..
make -j$(nproc)
sudo make install
```

## Verify the Installation

```bash
ldconfig -p | grep LivoxSdkCore
```

## Remove an Old Livox-SDK2 Installation

```bash
sudo rm -rf /usr/local/lib/liblivox_lidar_sdk_*
sudo rm -rf /usr/local/include/livox_lidar_*
```

## Prepare `livox_ros_driver2`

Before building the workspace:

```bash
cp ~/venom_ws/src/venom_vnv/driver/livox_ros_driver2/package_ROS2.xml \
   ~/venom_ws/src/venom_vnv/driver/livox_ros_driver2/package.xml
```

## Configure a Static NIC IP

Recommended static NIC settings for a MID360 link:

- Host NIC IP: `192.168.1.50`
- Netmask: `255.255.255.0`
- Gateway: `192.168.1.1`

The MID360 usually stays in the same subnet. Keep Wi-Fi online if you also need SSH or remote desktop at the same time.

## Update the MID360 Config File

Edit:

```text
~/venom_ws/src/venom_vnv/driver/livox_ros_driver2/config/MID360_config.json
```

Key fields to check:

```json
"cmd_data_ip": "192.168.1.50",
"push_msg_ip": "192.168.1.50",
"lidar_ip": "192.168.1.133"
```

- `cmd_data_ip` and `push_msg_ip` should match your host NIC IP
- `lidar_ip` must match the actual MID360 IP on your setup

## Validate the LiDAR Link

First test the network:

```bash
ping 192.168.1.133
```

Then launch a basic validation flow:

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch livox_ros_driver2 rviz_MID360_launch.py
```

## Next Step

If you also need boot-time routing, network priority, or automatic startup behavior, continue with [rc.local]({{ '/en/rc_local' | relative_url }}).

## Related Pages

- [Environment Setup]({{ '/en/environment' | relative_url }})
- [Livox LiDAR Driver]({{ '/en/livox_ros_driver2' | relative_url }})
- [Quick Start]({{ '/en/quick_start' | relative_url }})
