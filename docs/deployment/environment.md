---
title: 环境准备
description: Ubuntu、ROS 2 Humble、rosdep、VS Code、SSH、Clash 与 NoMachine 的准备流程。
---

## Ubuntu 安装参考

如果还没有系统环境，建议先参考这篇 Ubuntu 安装教程：

- [Ubuntu 安装教程](https://liyihan.xyz/archives/ubuntuan-zhuang-jiao-cheng)

下面的步骤默认你已经进入 Ubuntu 22.04 桌面系统。

## ROS 2 Humble / rosdep

先安装 ROS 2 Humble 和 `rosdep`，不要等到安装一堆软件之后再处理 ROS 环境。这样可以尽量避免后续依赖版本需要降级或回退。

```bash
sudo apt update
sudo apt install -y wget curl git
wget http://fishros.com/install -O fishros && . fishros
```

进入 FishROS 菜单后，选择安装 ROS 2，并选择 `humble` 版本；如果菜单中有 `rosdep` 相关选项，也一并完成初始化。如果看不懂，进去之后所有选项都选择 1。

如果后续 `rosdep install` 报错，先尝试：

```bash
sudo rosdep init
rosdep update
```

注意：VS Code 不建议通过 FishROS 菜单安装，下一节直接从 VS Code 官网下载 `.deb` 包。

## SSH 远程连接

安装 SSH 服务，方便后续远程登录 NUC 或开发机：

```bash
sudo apt update
sudo apt install -y openssh-server
sudo systemctl enable --now ssh
systemctl status ssh --no-pager
```

## VS Code

VS Code 直接从官网下载 `.deb` 包：

- [Visual Studio Code Download](https://code.visualstudio.com/Download)

在下载页面选择 Linux 下的 `.deb`，Ubuntu / NUC 通常选择 `x64`。浏览器默认会把文件放到 `~/Downloads`，因此下载完成后执行：

```bash
cd ~/Downloads
sudo apt install ./code_*_amd64.deb
```

如果文件名不完全一致，可以输入到 `./code_` 后按 `Tab` 自动补全。

## Clash Verge Rev

如需代理工具，可从 GitHub Releases 下载 Debian 系 `.deb` 包：

- [Clash Verge Rev Releases](https://github.com/Clash-Verge-rev/clash-verge-rev/releases)

在 Releases 页面选择 Linux 的 `DEB包(Debian系)`，x86_64 机器选择 `64位`。下载完成后执行：

```bash
cd ~/Downloads
sudo apt install ./Clash.Verge_*_amd64.deb
```

如果文件名不完全一致，可以输入到 `./Clash` 后按 `Tab` 自动补全。

## 远程桌面

NoMachine 从官网下载 Linux `.deb` 包：

- [NoMachine Download](https://www.nomachine.com/download)

备注：访问官网通常需要代理。

下载完成后执行：

```bash
cd ~/Downloads
sudo apt install ./nomachine_*_amd64.deb
```

如果文件名不完全一致，可以输入到 `./nomachine_` 后按 `Tab` 自动补全。

## 下一步

基础环境准备完成后，继续看 [雷达配置](lidar_setup.md).
