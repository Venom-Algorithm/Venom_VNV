---
title: Environment Setup
description: Software versions, prerequisite tools, and hardware preparation notes.
---

## Recommended Software Environment

- Ubuntu 22.04
- ROS 2 Humble
- `colcon`
- `rosdep`
- Livox-SDK2

## Basic Preparation

If you need a complete Ubuntu setup walkthrough, you can start from this guide:

- [Ubuntu installation guide](https://liyihan.xyz/archives/ubuntuan-zhuang-jiao-cheng)

After that, the project currently recommends preparing:

- `openssh-server`
- ROS 2 Humble
- `rosdep`
- VS Code

One practical way used by the project is:

```bash
sudo apt update
wget http://fishros.com/install -O fishros && . fishros
```

## Additional Tools Often Used in Development

### Clash Verge Rev

- [Clash Verge Rev Releases](https://github.com/Clash-Verge-rev/clash-verge-rev/releases)

### NoMachine

- Official site: [NoMachine](https://www.nomachine.com/)
- A VPN or proxy may be required to access the site from some regions

Typical install flow:

```bash
cd ~/Downloads
sudo apt install ./xxxx.deb
```

## Hardware Prerequisites

- Livox Mid360
- Hikrobot USB3 industrial camera
- Scout Mini chassis
- NUC ↔ DJI controller serial link

Recommended extras:

- A wired NIC that can be configured with a static IP
- A CAN adapter
- Stable serial device paths

## Next Step

After the software environment is ready, continue with [LiDAR Setup](lidar_setup.md).
