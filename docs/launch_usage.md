---
title: 启动使用
desc: 完成编译后的首次启动入口与常用运行命令。
breadcrumb: 首页
layout: default
---

## 开始之前

默认你已经完成：

- [快速开始]({{ '/quick_start' | relative_url }})
- 需要时完成 [配置雷达]({{ '/lidar_setup' | relative_url }})
- 需要时完成 [底盘 CAN 部署]({{ '/chassis_can_setup' | relative_url }})

## 进入工作空间

```bash
cd ~/venom_ws
source install/setup.bash
```

## 更新到最新版本

如果你已经在另一台机器上拉过仓库，后续想把主仓库和全部子模块一起更新到当前最新版本，可以执行：

```bash
cd ~/venom_ws/src/venom_vnv
git pull origin master
git submodule sync --recursive
git submodule update --init --recursive
```

## 常用启动命令

### 1. 雷达驱动验证

```bash
ros2 launch livox_ros_driver2 rviz_MID360_launch.py
```

### 2. 底盘驱动验证

```bash
ros2 launch scout_base scout_mini_base.launch.py
```

### 3. 自瞄测试

```bash
ros2 launch venom_bringup autoaim_test_bringup.launch.py
```

### 4. 建图

```bash
ros2 launch venom_bringup mapping_bringup.launch.py
```

### 5. 重定位

```bash
ros2 launch venom_bringup relocalization_bringup.launch.py
```

### 6. 导航 + 自瞄

```bash
ros2 launch venom_bringup autoaim_nav_bringup.launch.py
```

## 建议阅读顺序

如果你只是第一次联调，建议按这个顺序来：

1. 先跑雷达
2. 再跑底盘
3. 再跑自瞄测试
4. 最后再进入整机模式

## 进一步阅读

- 启动入口设计：参考 [系统集成]({{ '/integration_overview' | relative_url }})
- 不同模式说明：参考 [运行模式]({{ '/run_modes' | relative_url }})
