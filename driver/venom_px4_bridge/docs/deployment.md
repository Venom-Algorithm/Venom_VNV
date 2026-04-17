# PX4 Deployment

This is the deployment guide for the VNV PX4 integration project.

## Project Packages

The project contains two ROS packages:

- `driver/venom_px4_bridge/px4_msgs`
- `driver/venom_px4_bridge/venom_px4_bridge`

The first is vendored upstream message definitions.

The second is the VNV bridge implementation.

## Official References

- PX4 ROS 2 User Guide: <https://docs.px4.io/main/zh/ros2/user_guide>
- PX4 uXRCE-DDS middleware guide: <https://docs.px4.io/main/en/middleware/uxrce_dds>
- PX4 `px4_msgs`: <https://github.com/PX4/px4_msgs>
- PX4 `px4_ros_com`: <https://github.com/PX4/px4_ros_com>

## Prerequisites

- Ubuntu `22.04`
- ROS 2 `Humble`
- PX4 firmware line `v1.16.x`
- `Micro XRCE-DDS Agent v2.4.3`

## Step 1. Install ROS Dependencies

```bash
sudo apt update
rosdep update
cd ~/venom_ws
rosdep install -r --from-paths src --ignore-src --rosdistro humble -y
```

## Step 2. Install Micro XRCE-DDS Agent

```bash
cd /tmp
git clone https://github.com/eProsima/Micro-XRCE-DDS-Agent.git
cd Micro-XRCE-DDS-Agent
git checkout v2.4.3
mkdir -p build
cd build
cmake ..
make -j$(nproc)
sudo make install
sudo ldconfig
```

Expected command after installation:

```bash
MicroXRCEAgent udp4 -p 8888
```

## Step 3. Build The PX4 Slice

```bash
cd ~/venom_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install --packages-up-to px4_msgs venom_px4_bridge venom_bringup
source install/setup.bash
```

## Step 4. Start PX4 SITL Or Hardware DDS Client

Make sure PX4 has `uxrce_dds_client` active and configured to match the companion-side agent transport.

The default VNV probe launch assumes:

- transport: `udp4`
- port: `8888`

## Step 5. Run The Probe Stack

```bash
source /opt/ros/humble/setup.bash
source ~/venom_ws/install/setup.bash
ros2 launch venom_bringup px4_agent_probe.launch.py
```

If the agent is already running elsewhere:

```bash
ros2 launch venom_bringup px4_agent_probe.launch.py start_agent:=false
```

If the PX4 link uses serial:

```bash
ros2 launch venom_bringup px4_agent_probe.launch.py \
  agent_transport:=serial \
  agent_device:=/dev/ttyUSB0 \
  agent_baudrate:=921600
```

## Step 6. Verify Topics

```bash
ros2 topic list | grep '^/fmu/'
ros2 topic echo /px4_bridge/agent_status
ros2 topic echo /px4_bridge/health
ros2 topic echo /px4_bridge/state
ros2 topic echo /px4_bridge/odom
```

Expected bridge-level outputs:

- `/px4_bridge/agent_status`
- `/px4_bridge/health`
- `/px4_bridge/state`
- `/px4_bridge/odom`

Expected minimum PX4 DDS outputs:

- `/fmu/out/vehicle_status`
- `/fmu/out/vehicle_odometry`
- `/fmu/out/timesync_status`

## Real Hardware Checklist

Before offboard or external-pose work, confirm:

1. PX4 firmware line is still `v1.16.x`
2. vendored `px4_msgs` is still based on the documented upstream commit
3. `MicroXRCEAgent` transport matches PX4 `uxrce_dds_client`
4. PX4 parameter `UXRCE_DDS_CFG` is configured so DDS actually starts
5. topic namespace is `/fmu` unless intentionally remapped
6. `TimesyncStatus` is continuous, not one-shot
7. downstream consumers expect ROS ENU/FLU, not PX4 NED/FRD
