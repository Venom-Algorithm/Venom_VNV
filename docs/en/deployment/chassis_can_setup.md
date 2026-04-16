---
title: Chassis CAN Setup
permalink: /en/chassis_can_setup
desc: Initialize the chassis CAN adapter, bring up the interface, and validate the Scout chain.
breadcrumb: Deployment & Usage
layout: default
---

## Scope

This page mainly targets:

- Scout Mini
- Scout Mini Omni
- CAN-based chassis communication
- `scout_ros2 + ugv_sdk`

## First-Time CAN Adapter Setup

The repository already includes helper scripts in `ugv_sdk`:

```text
driver/ugv_sdk/scripts/setup_can2usb.bash
```

You can run:

```bash
bash ~/venom_ws/src/venom_vnv/driver/ugv_sdk/scripts/setup_can2usb.bash
```

The script essentially performs:

```bash
sudo modprobe gs_usb
sudo ip link set can0 up type can bitrate 500000
sudo apt install -y can-utils
```

## Bring Up `can0` After Replugging

```bash
bash ~/venom_ws/src/venom_vnv/driver/ugv_sdk/scripts/bringup_can2usb_500k.bash
```

Equivalent command:

```bash
sudo ip link set can0 up type can bitrate 500000
```

## Check the CAN Interface

```bash
ifconfig -a | grep can
ip -details link show can0
```

## Debugging Tips

```bash
candump can0
```

If the bus is healthy, you should see chassis-related CAN frames.

## Launch the ROS 2 Chassis Node

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch scout_base scout_mini_base.launch.py
```

Other common variants:

```bash
ros2 launch scout_base scout_base.launch.py
ros2 launch scout_base scout_mini_omni_base.launch.py
```

## Keyboard Teleop Test

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

## Common Issues

### `can0` is missing

- Check whether the adapter is plugged in
- Run `sudo modprobe gs_usb`
- Run the setup script again

### `can0` exists but the chassis does not respond

- Confirm the bitrate is `500000`
- Check the remote-controller mode and E-stop
- Use `candump can0` to inspect frame traffic

### CAN needs to be reconfigured after every boot

If you want boot-time setup, combine this page with [rc.local]({{ '/en/rc_local' | relative_url }}).

## Related Pages

- [Chassis Driver Overview]({{ '/en/chassis_driver' | relative_url }})
- [rc.local]({{ '/en/rc_local' | relative_url }})
