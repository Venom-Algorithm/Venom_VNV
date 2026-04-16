---
title: rc.local
permalink: /rc_local
desc: Ubuntu 22.04 中启用 rc.local，并用于开机执行网络优先级等初始化命令。
breadcrumb: 部署与使用
layout: default
---

## rc.local 的基本概念

### 定义与作用

`rc.local` 是传统的 Linux 启动脚本，通常位于 `/etc/rc.local`，用于在系统启动的最后阶段执行自定义命令或脚本。

它常用于：

- 启动自定义服务
- 挂载设备
- 设置环境变量
- 执行网络初始化命令

### 执行时机与权限

- 在系统启动完成后、用户登录前执行
- 默认以 `root` 权限运行
- 文件需要具有可执行权限

```bash
chmod +x /etc/rc.local
```

## Ubuntu 22.04 启用 rc.local

Ubuntu 22.04 默认没有启用 `rc.local`，需要手动配置。

### 1. 创建 rc.local 文件

```bash
sudo touch /etc/rc.local
sudo chmod 755 /etc/rc.local
echo '#!/bin/bash' | sudo tee /etc/rc.local
```

### 2. 配置 rc-local 服务

将 `rc-local.service` 复制到系统目录：

```bash
sudo cp /usr/lib/systemd/system/rc-local.service /etc/systemd/system/
```

编辑服务文件：

```bash
code /etc/systemd/system/rc-local.service
```

在 `[Install]` 部分添加：

```ini
[Install]
WantedBy=multi-user.target
```

### 3. 启用并启动服务

```bash
sudo systemctl start rc-local
sudo systemctl enable rc-local
sudo systemctl status rc-local
```

如果状态显示 `active (running)`，说明服务已经正常启用。

### 4. 添加开机自启动脚本

编辑：

```bash
code /etc/rc.local
```

示例：

```bash
#!/bin/bash
echo "系统启动中..."
# 添加你需要加入的东西
exit 0
```

注意最后一行需要保留：

```bash
exit 0
```

### 5. 重启系统验证

```bash
sudo reboot
```

## 用于网络优先级设置

如果有线网卡连接雷达后影响默认网络路由，可以把相关命令放进 `rc.local`。

例如删除某条有线网段路由：

```bash
sudo ip route del 192.168.1.0/24 dev enp86s0
```

例如增加一条指向 Mid360 的静态路由：

```bash
sudo ip route add 192.168.1.133 dev enp88s0 proto kernel scope link src 192.168.1.50 metric 100
```

可以把这些命令写进 `/etc/rc.local`，例如：

```bash
#!/bin/bash
ip route add 192.168.1.133 dev enp88s0 proto kernel scope link src 192.168.1.50 metric 100
exit 0
```

如果你需要同时处理网络优先级和雷达配置，建议结合 [配置雷达]({{ '/lidar_setup' | relative_url }}) 一起查看。

## 注意事项

- 脚本需要可执行权限
- `rc.local` 以 `root` 权限执行，命令要谨慎
- 网卡名如 `enp86s0`、`enp88s0` 需要按你自己的机器实际情况修改
