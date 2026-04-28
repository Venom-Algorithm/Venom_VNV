---
title: Environment Setup
description: Ubuntu, ROS 2 Humble, rosdep, VS Code, SSH, Clash, and NoMachine setup.
---

## Ubuntu Reference

If you still need to install Ubuntu, start from this guide:

- [Ubuntu installation guide](https://liyihan.xyz/archives/ubuntuan-zhuang-jiao-cheng)

The steps below assume you are already in an Ubuntu 22.04 desktop session.

## ROS 2 Humble / rosdep

Install ROS 2 Humble and `rosdep` first. Doing this before installing a large set of extra software reduces the chance of dependency downgrades later.

```bash
sudo apt update
sudo apt install -y wget curl git
wget http://fishros.com/install -O fishros && . fishros
```

In the FishROS menu, install ROS 2 and select `humble`. If the menu provides `rosdep` initialization, run it as well.

If `rosdep install` fails later, try:

```bash
sudo rosdep init
rosdep update
```

Do not install VS Code from the FishROS menu. Install it from the official VS Code download page in the next section.

## SSH Remote Access

Install SSH so the machine can be accessed remotely:

```bash
sudo apt update
sudo apt install -y openssh-server
sudo systemctl enable --now ssh
systemctl status ssh --no-pager
```

## VS Code

Download the `.deb` package from the official page:

- [Visual Studio Code Download](https://code.visualstudio.com/Download)

Choose the Linux `.deb` package. For most Ubuntu NUC machines, choose `x64`. Browsers usually download it to `~/Downloads`, so install it with:

```bash
cd ~/Downloads
sudo apt install ./code_*_amd64.deb
```

If the file name differs, type `./code_` and press `Tab` to complete the file name.

### Clash Verge Rev

- [Clash Verge Rev Releases](https://github.com/Clash-Verge-rev/clash-verge-rev/releases)

Choose the Linux Debian `.deb` package. For x86_64 machines, choose the 64-bit package. After downloading:

```bash
cd ~/Downloads
sudo apt install ./Clash.Verge_*_amd64.deb
```

If the file name differs, type `./Clash` and press `Tab` to complete the file name.

### NoMachine

- [NoMachine Download](https://www.nomachine.com/download)

A VPN or proxy may be required to access the site from some regions.

Download the Linux `.deb` package and install it with:

```bash
cd ~/Downloads
sudo apt install ./nomachine_*_amd64.deb
```

If the file name differs, type `./nomachine_` and press `Tab` to complete the file name.

## Next Step

After the software environment is ready, continue with [LiDAR Setup](lidar_setup.md).
