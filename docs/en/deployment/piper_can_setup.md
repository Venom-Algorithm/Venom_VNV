---
title: Arm CAN Setup
permalink: /en/piper_can_setup
desc: Detect, name, bring up, and validate the Piper CAN interface.
breadcrumb: Deployment & Usage
layout: default
---

## Scope

This page targets:

- AgileX Piper robotic arm
- The official USB-to-CAN module shipped for the arm
- `piper_ros` single-arm control workflows

## Install Dependencies

```bash
sudo apt update
sudo apt install -y can-utils ethtool
sudo apt install -y iproute2
```

## Find the CAN Module

```bash
cd ~/venom_ws/src/venom_vnv/driver/piper_ros
bash find_all_can_port.sh
```

Typical output:

```bash
Both ethtool and can-utils are installed.
Interface can0 is connected to USB port 3-1.4:1.0
```

Record the USB port ID. It is the safest way to distinguish the arm adapter from chassis CAN adapters on the same machine.

## Recommended Single-Arm Naming

To avoid conflicts with chassis CAN, the project recommends naming the arm interface `can_piper`:

```bash
cd ~/venom_ws/src/venom_vnv/driver/piper_ros
bash can_activate.sh can_piper 1000000
```

If you explicitly want the default interface name, use:

```bash
bash can_activate.sh can0 1000000
```

## Arm and Chassis on the Same Machine

Recommended naming:

- Chassis: `can0`
- Piper arm: `can_piper`

If multiple CAN devices are present, use the USB port ID to activate the correct one:

```bash
cd ~/venom_ws/src/venom_vnv/driver/piper_ros
bash can_activate.sh can_piper 1000000 "3-1.4:1.0"
```

## Multiple Arm CAN Modules

The repository also includes:

```bash
can_muti_activate.sh
```

Edit the `USB_PORTS` mapping in that script, for example:

```bash
USB_PORTS["3-1.1:1.0"]="can_arm1:1000000"
USB_PORTS["3-1.2:1.0"]="can_arm2:1000000"
```

Then run:

```bash
bash can_muti_activate.sh
```

## Check the Interface

```bash
ifconfig -a | grep can
ip -details link show can_piper
```

## Basic Debugging

```bash
candump can_piper
```

If the arm is powered and the link is healthy, you should normally see CAN traffic.

## Launch the Arm Node

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch piper start_single_piper.launch.py can_port:=can_piper
```

With RViz:

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch piper start_single_piper_rviz.launch.py can_port:=can_piper
```

## Related Pages

- [Piper Arm Driver]({{ '/en/piper_ros' | relative_url }})
- [Chassis CAN Setup]({{ '/en/chassis_can_setup' | relative_url }})
- [rc.local]({{ '/en/rc_local' | relative_url }})
