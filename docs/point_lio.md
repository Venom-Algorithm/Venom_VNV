---
title: Point-LIO
desc: Point-LIO — 高带宽激光惯性里程计配置步骤。
breadcrumb: 定位建图
layout: default
---

### 7. 第七步：配置 Point-LIO
把 Point-LIO 放进localization 目录：
```bash
cd ~/ros2_ws/src/localization
git clone https://github.com/HY-LiYihan/point-LIO
```
这样路径是：
```
~/ros2_ws/src/localization/point_lio
```
### 安装依赖库
```bash
sudo apt install -y \
ros-humble-pcl-conversions \
libeigen3-dev \
ros-humble-pcl-ros \
ros-humble-tf2-ros \
libusb-1.0-0-dev
```
安装 ROS 2 Humble 版本的 PCL（Point Cloud Library）转换库：
```bash
sudo apt-get install libeigen3-dev
```
安装 Eigen3 线性代数库的开发版本
### 依赖安装与初始化
```bash
rosdep install -r --from-paths src --ignore-src --rosdistro $ROS_DISTRO
```
自动安装 src 目录下所有 ROS 2 包的系统级依赖
```bash
sudo rosdep init
```
初始化 rosdep 工具（ROS 依赖管理工具）
```bash
rosdep install -r --from-paths src --ignore-src --rosdistro $ROS_DISTRO
```
再次执行依赖安装，确保所有依赖都已安装完成
### 一键配置工具（鱼香ROS）
```bash
wget http://fishros.com/install -O fishros && . fishros
```
下载并运行鱼香ROS（FishROS）一键配置脚本
### 编译 ROS 2 工作空间
```bash
cd ros2_ws/
source install/setup.bash
# 再次进入工作空间并加载环境变量
colcon build --symlink-install -DCMAKE_BUILD_TYPE=Release
# 编译 ROS 2 工作空间
source install/setup.bash
# 重新加载环境变量
```
### rc.local配置（启动项管理）
附上链接：
- [rc.local配置(启动项管理)](rc.local配置(启动项管理))
### 松灵mini遥控器使用说明
[松灵mini遥控器使用说明](https://new.agilex.ai/raw/upload/20230718/SCOUT%20MINI%E7%94%A8%E6%88%B7%E6%89%8B%E5%86%8C20230718_74957.pdf)
