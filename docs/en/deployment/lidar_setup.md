---
title: LiDAR Setup
description: Install Livox-SDK2, configure MID360 networking, and validate the LiDAR
  chain.
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
sudo ldconfig
```

## Verify the Installation

`ldconfig -p | grep LivoxSdkCore` is not a reliable check for the current Livox-SDK2 installation. Check the library files that `livox_ros_driver2` actually links against:

```bash
ls /usr/local/lib/liblivox_lidar_sdk_shared.so
ls /usr/local/lib/liblivox_lidar_sdk_static.a
```

If `liblivox_lidar_sdk_shared.so` exists, the key runtime library required by the ROS 2 driver is installed.

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

## Useful `livox_ros_driver2` Commands

The standard Venom VNV build still uses the root workspace `colcon build` command from [Quick Start](../home/quick_start.md). The upstream `livox_ros_driver2` README also provides a standalone build script for driver-only checks:

```bash
cd ~/venom_ws/src/venom_vnv/driver/livox_ros_driver2
source /opt/ros/humble/setup.bash
./build.sh humble
```

This script cleans `~/venom_ws/build`, `~/venom_ws/install`, and related build directories. For normal full-workspace builds, keep using the main repository build command.

The upstream ROS 2 launch format is:

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch livox_ros_driver2 <launch_file>
```

Useful MID360 launch files:

| Command | Purpose |
| --- | --- |
| `ros2 launch livox_ros_driver2 rviz_MID360_launch.py` | Connect to MID360, publish PointCloud2 data, and open RViz |
| `ros2 launch livox_ros_driver2 msg_MID360_launch.py` | Connect to MID360 and publish Livox custom point cloud messages |

If the driver reports `cannot open shared object file`, add `/usr/local/lib` in the current terminal:

```bash
export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:/usr/local/lib
```

## Configure a Static NIC IP

Recommended static NIC settings for a MID360 link:

- Host NIC IP: `192.168.1.50`
- Netmask: `255.255.255.0`
- Gateway: `192.168.1.1`

The MID360 usually stays in the same subnet. Keep Wi-Fi online if you also need SSH or remote desktop at the same time.

## Configure LiDAR Route Priority

When the computer uses both Wi-Fi and the wired LiDAR NIC, Linux may add a full `192.168.1.0/24` route to the wired NIC. For field debugging, remove that full subnet route and add a host route only for the actual MID360 IP.

Check the current route table first:

```bash
ip route
```

Find the wired NIC route for the LiDAR subnet. It usually looks like:

```text
192.168.1.0/24 dev enp3s0 proto kernel scope link src 192.168.1.50 metric 100
```

Do not copy the example commands blindly. The NIC name, host IP, metric, and LiDAR IP can differ on every machine. Copy the NIC name from your own `ip route` output and replace the LiDAR IP with the actual one.

Delete the full subnet route on the wired NIC:

```bash
sudo ip route del 192.168.1.0/24 dev enp3s0
```

Then add a host route to the LiDAR only. This example uses LiDAR IP `192.168.1.133`, host wired IP `192.168.1.50`, and NIC `enp3s0`:

```bash
sudo ip route add 192.168.1.133/32 dev enp3s0 src 192.168.1.50 metric 100
```

Verify that LiDAR traffic uses the wired NIC:

```bash
ip route get 192.168.1.133
ping 192.168.1.133
```

If the route should be restored after every reboot, put the delete and add commands into [rc.local](rc_local.md).

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

If you also need boot-time routing, network priority, or automatic startup behavior, continue with [rc.local](rc_local.md).

## Related Pages

- [Environment Setup](environment.md)
- [Livox LiDAR Driver](../modules/drivers/livox_ros_driver2.md)
- [Quick Start](../home/quick_start.md)
