---
title: RealSense 配置
description: Intel RealSense D435 / D435i 的 librealsense、ROS 2 wrapper 与仓库内基础验证流程。
---

## 适用范围

这页主要面向：

- Intel RealSense D435 / D435i
- 需要在 Ubuntu 22.04 + ROS 2 Humble 下完成基础驱动安装
- 需要在本仓库里使用 `venom_bringup` 的 `d435i_test.launch.py` 做验证

以下步骤主要参考官方的 Linux 手动安装说明与 ROS wrapper 安装说明整理。

官方参考：

- [librealsense Linux manual installation guide](https://github.com/realsenseai/librealsense/blob/master/doc/distribution_linux.md#installing-the-packages)
- [realsense-ros 官方仓库](https://github.com/realsenseai/realsense-ros)

## 安装 librealsense 软件源与密钥

```bash
sudo mkdir -p /etc/apt/keyrings

curl -sSf https://librealsense.realsenseai.com/Debian/librealsenseai.asc | \
gpg --dearmor | sudo tee /etc/apt/keyrings/librealsenseai.gpg > /dev/null
```

说明：

- 这一步会把 RealSense 软件源公钥写入 `/etc/apt/keyrings/librealsenseai.gpg`
- 新 keyring 同时兼容新的 RS 公钥和旧的 Intel 公钥

## 安装 APT HTTPS 支持

```bash
sudo apt-get update
sudo apt-get install -y apt-transport-https
```

## 添加 RealSense 软件源

```bash
echo "deb [signed-by=/etc/apt/keyrings/librealsenseai.gpg] https://librealsense.realsenseai.com/Debian/apt-repo `lsb_release -cs` main" | \
sudo tee /etc/apt/sources.list.d/librealsense.list

sudo apt-get update
```

## 安装运行时包

```bash
sudo apt-get install -y librealsense2-dkms
sudo apt-get install -y librealsense2-utils
```

这两项会完成：

- udev 规则部署
- 内核模块构建与激活
- 运行时库安装
- 常用工具安装，例如 `realsense-viewer`

## 可选开发包

如果你后续还要自己编译基于 librealsense 的程序，可继续安装：

```bash
sudo apt-get install -y librealsense2-dev
sudo apt-get install -y librealsense2-dbg
```

装好 `librealsense2-dev` 后，通常可以直接用如下形式链接：

```bash
g++ -std=c++11 filename.cpp -lrealsense2
```

## 安装 ROS 2 wrapper

本仓库中的 [`d435i_test.launch.py`](https://github.com/Venom-Algorithm/Venom_VNV/blob/master/venom_bringup/launch/examples/d435i_test.launch.py) 会调用 `realsense2_camera` 包，所以还需要准备对应的 ROS 2 wrapper。

官方 `realsense-ros` 文档给出的 Debian 安装方式是：

```bash
sudo apt update
sudo apt install -y ros-$ROS_DISTRO-realsense2-*
```

如果你的环境变量还没有设置，也可以直接写成 Humble 对应形式：

```bash
sudo apt update
sudo apt install -y ros-humble-realsense2-*
```

## 安装完成后的基础验证

重新插拔 RealSense 相机后，先执行：

```bash
realsense-viewer
```

如果 `realsense-viewer` 能正常打开并识别相机，说明 `librealsense2-utils` 部分基本已经就绪。

然后再检查内核模块版本：

```bash
modinfo uvcvideo | grep "version:"
```

正常情况下，输出中应包含 `realsense` 字样。

## 仓库内验证

如果你还需要验证本仓库里的调用链路，可以直接运行：

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch venom_bringup d435i_test.launch.py
```

这个 launch 当前默认会：

- 使用 `realsense2_camera/launch/rs_launch.py`
- 默认命名空间为 `camera`
- 默认相机名为 `d435i`
- 默认开启 `color`、`depth`、`gyro`、`accel`
- 默认开启点云输出
- 默认开启 RViz

## 常见检查项

- `realsense-viewer: command not found`
  说明通常是 `librealsense2-utils` 没有装好。

- `Package 'realsense2_camera' not found`
  说明 ROS 2 wrapper 还没有安装，先执行上面的 `ros-$ROS_DISTRO-realsense2-*` 安装命令。

- `modinfo uvcvideo` 结果里没有 `realsense`
  说明 `librealsense2-dkms` 没有正确生效。建议重新安装后重插相机，必要时重启系统。

- 相机已被系统识别，但 `d435i_test.launch.py` 起不来
  先单独检查 `realsense-viewer` 是否正常，再检查 `realsense2_camera` 包是否存在。

## 相关文档

- [环境准备](environment.md)
- [启动使用](../home/launch_usage.md)
