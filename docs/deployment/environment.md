---
title: 环境准备
description: 软件版本、依赖项和硬件前置条件。
---

## Ubuntu 安装参考

如果还没有系统环境，建议先参考这篇 Ubuntu 安装教程：

- [Ubuntu 安装教程](https://liyihan.xyz/archives/ubuntuan-zhuang-jiao-cheng)

## 基础工具

首先安装 SSH 服务，方便远程连接：

```bash
sudo apt update
sudo apt install -y openssh-server
```

## ROS 2 / rosdep / VS Code

建议使用 FishROS 一键安装 ROS、`rosdep` 和 VS Code：

```bash
sudo apt update
wget http://fishros.com/install -O fishros && . fishros
```

## 网络工具

如需科学上网，可从以下地址下载 Clash Verge Rev：

- [Clash Verge Rev Releases](https://github.com/Clash-Verge-rev/clash-verge-rev/releases)

## 远程桌面

NoMachine 官网：

- [https://www.nomachine.com/](https://www.nomachine.com/)

备注：访问官网通常需要挂梯子。

下载安装 `.deb` 包后，可执行：

```bash
cd ~/Downloads
sudo apt install ./xxxx
```

## 下一步

基础环境准备完成后，继续看 [雷达配置](lidar_setup.md).
