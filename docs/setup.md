---
title: 装配配置
desc: 从零开始搭建开发环境，安装 SDK、编译工作空间、配置硬件。
breadcrumb: 快速开始
layout: default
---

## ⚙️ 装配步骤

### 1. 第一步：安装 Livox-SDK2

```bash
cd ~
sudo apt update
sudo apt install -y cmake git
git clone https://github.com/Livox-SDK/Livox-SDK2.git
cd Livox-SDK2
mkdir -p build
cd build
cmake ..
make -j$(nproc)
sudo make install
```

将驱动放入 drivers 目录：

```bash
cd ~/ros2_ws/src/drivers
git clone https://github.com/Livox-SDK/livox_ros_driver2.git
```

路径如下：

```
~/ros2_ws/src/drivers/livox_ros_driver2
```

编译驱动：

```bash
cd ~/ros2_ws/src/drivers/livox_ros_driver2
source /opt/ros/humble/setup.sh
./build.sh humble
```

### 2. 第二步：编译工作空间

```bash
cd ~/ros2_ws/src/drivers/livox_ros_driver2
cp package_ROS2.xml package.xml
cd ~/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install --cmake-args -DROS_EDITION=ROS2 -DHUMBLE_ROS=humble
source ~/ros2_ws/install/setup.bash
ros2 pkg list | grep livox
```

### 3. 第三步：配置网卡静态 IP

在 ROS2 中配置 MID360 雷达：

```
雷达 IP：192.168.1.133
```

电脑有线网卡配置：

```
IP：192.168.1.50
```

- 子网掩码：`255.255.255.0`
- 网关：`192.168.1.1`

WiFi 保持正常联网，用于 SSH 连接

测试雷达网络：

```bash
ping 192.168.1.233
```

### 4. 第四步：修改 MID360 配置文件

打开：

```
ros2_ws/src/drivers/livox_ros_driver2/config/MID360_config.json
```

修改：

```json
"cmd_data_ip": "192.168.1.50",
"push_msg_ip": "192.168.1.50",
"lidar_ip": "192.168.1.133"
```

打开：

```
ros2_ws/install/livox_ros_driver2/share/livox_ros_driver2/config/MID360_config.json
```

同样修改：

- `192.168.1.50`
- `192.168.1.133`

### 5. 第五步：网络配置

1. 打开网络设置
2. 选择有线连接，点击设置图标
3. 在 IPv4 标签页中选择 "手动"
4. 配置以下参数：
   - IP 地址：`192.168.1.5`
   - 子网掩码：`255.255.255.0`
   - 网关：`192.168.1.254`

测试连接

⚠️ 注意

假设 MID360 序列号为 47MDLAS0020103，则 IP 为 `192.168.1.103`
若序列号不同，则 IP 为 `192.168.1.1xx`（xx 为序列号后两位）

## 测试与雷达的连接

```bash
ping 192.168.1.103
```

### 网络优先级调整

📌 由于有线连接可能导致无法连接 NoMachine，这里提供解决方案

```bash
ip route
```

![网络优先级](../assets/1752651964814.png)

删除有线网络路由：

```bash
sudo ip route del 192.168.1.0/24 dev enp86s0
```

所以此时再运行如下：

![代码](../assets/image.png)

### 6. 第六步：参数设置
将雷达地址解析到有线连接，运行命令：
```bash
sudo ip route add 192.168.1.133 dev enp88s0 proto kernel scope link src 192.168.1.50 metric 100
```
接下来修改 `livox_ros_driver2` 中的一些配置：
- **蓝色划线**与静态 IP 一致：`192.168.1.50`
- **红色划线**为 `192.168.1.1xx`，后两位为 MID360 最后两位广播码
> 这个雷达的 IP 是 `192.168.1.1XX`
> 这个雷达的序列号通过扫码获得
需要修改的文件：
```
livox_ros_driver2/config/MID360_config.json
```
![代码](../assets/1.png)

livox_ros_driver2/launch_ROS2/rviz_MID360.launch 

![代码](../assets/2.png)

livox_ros_driver2/launch_ROS2/msg_MID360.launch

![代码](../assets/2.png)

此时配置已经结束，可以尝试在工作空间跑以下指令：
```bash
cd ~/ros2_ws
source install/setup.bash
# 启动MID360驱动
ros2 launch livox_ros_driver2 msg_MID360_launch.py
```
