---
title: 机械臂 CAN 部署
description: Piper 机械臂的 CAN 接口识别、命名、拉起与基础验证。
---

## 适用范围

本页主要针对：

- AgileX Piper 机械臂
- 使用机械臂官方 USB 转 CAN 模块
- 使用 `piper_ros` 进行单臂控制

如果当前机器还同时连接了底盘 CAN，请重点看“机械臂与底盘同时使用”这一节。

## 安装依赖

先安装 CAN 相关工具：

```bash
sudo apt update
sudo apt install -y can-utils ethtool
```

如果脚本执行时提示 `ip: command not found`，还需要安装：

```bash
sudo apt install -y iproute2
```

## 查找机械臂 CAN 模块

`piper_ros` 已经提供了一个用于识别 CAN 模块 USB 端口的脚本：

```bash
cd ~/venom_ws/src/venom_vnv/driver/piper_ros
bash find_all_can_port.sh
```

如果识别正常，你会看到类似输出：

```bash
Both ethtool and can-utils are installed.
Interface can0 is connected to USB port 3-1.4:1.0
```

这里最重要的是记录机械臂 CAN 模块对应的 `USB port`，例如：

- `3-1.4:1.0`

后面如果同一台机器还要同时接底盘 CAN，就靠这个地址区分不同模块。

## 单机械臂推荐配置

如果当前机器只连接了一个机械臂 CAN 模块，推荐直接把它命名成 `can_piper`，这样后续和底盘链路不会混淆。

```bash
cd ~/venom_ws/src/venom_vnv/driver/piper_ros
bash can_activate.sh can_piper 1000000
```

说明：

- `can_piper`：推荐给机械臂使用的接口名
- `1000000`：Piper 机械臂常用 CAN 波特率，通常不要改

如果你明确希望继续沿用默认名 `can0`，也可以这样：

```bash
bash can_activate.sh can0 1000000
```

## 机械臂与底盘同时使用

如果一台机器同时接机械臂 CAN 和底盘 CAN，推荐做法是：

- 底盘保留 `can0`
- 机械臂单独命名为 `can_piper`

步骤如下。

### 1. 先确认机械臂 CAN 的 USB 端口

只插机械臂 CAN 模块，执行：

```bash
cd ~/venom_ws/src/venom_vnv/driver/piper_ros
bash find_all_can_port.sh
```

记录输出中的 USB 端口，例如：

```bash
Interface can0 is connected to USB port 3-1.4:1.0
```

### 2. 按 USB 端口精确激活机械臂 CAN

```bash
cd ~/venom_ws/src/venom_vnv/driver/piper_ros
bash can_activate.sh can_piper 1000000 "3-1.4:1.0"
```

这样即使系统里同时存在多个 CAN 设备，也会只把指定 USB 口上的那个接口重命名并拉起为 `can_piper`。

## 多机械臂场景

如果你需要同时连接多个机械臂 CAN 模块，可以使用：

```bash
cd ~/venom_ws/src/venom_vnv/driver/piper_ros
```

先修改脚本里的 `USB_PORTS` 映射：

```bash
can_muti_activate.sh
```

脚本里默认类似这样：

```bash
USB_PORTS["3-1.1:1.0"]="can_arm1:1000000"
USB_PORTS["3-1.2:1.0"]="can_arm2:1000000"
```

把 USB 端口改成你自己机器上的实际值后，再执行：

```bash
bash can_muti_activate.sh
```

## 检查接口是否正常

确认接口已经拉起：

```bash
ifconfig -a | grep can
```

查看接口详细状态：

```bash
ip -details link show can_piper
```

如果你使用的是其他名字，请把 `can_piper` 替换成实际接口名。

## 基础调试

可以先直接监听 CAN 总线：

```bash
candump can_piper
```

如果机械臂已上电且链路正常，通常应该能看到相关 CAN 帧。

## 启动机械臂 ROS 2 节点

基础启动：

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch piper start_single_piper.launch.py can_port:=can_piper
```

如果希望同时打开 RViz：

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch piper start_single_piper_rviz.launch.py can_port:=can_piper
```

如果你实际使用的是 `can0`，就把 `can_port:=can_piper` 改成：

```bash
can_port:=can0
```

## 常见问题

### 找不到机械臂 CAN 接口

- 检查 CAN 模块是否已经插入
- 重新执行 `bash find_all_can_port.sh`
- 检查 `ethtool`、`can-utils` 是否已安装

### 接口存在但名字不对

- 重新执行 `bash can_activate.sh can_piper 1000000`
- 如果系统里有多个 CAN 设备，补上 USB 端口参数

### 接口能拉起但机械臂没有响应

- 确认波特率是否为 `1000000`
- 确认机械臂是否已经正常上电
- 先用 `candump can_piper` 看是否有数据
- 再检查 launch 中传入的 `can_port` 是否和接口名一致

### 每次重启后接口名都乱掉

如果你希望开机时自动配置机械臂 CAN，可以结合 [rc.local](rc_local.md) 使用，把激活命令写进去。

## 相关文档

- [Piper 机械臂驱动](../modules/drivers/piper_ros.md)
- [底盘 CAN 部署](chassis_can_setup.md)
- [rc.local](rc_local.md)
