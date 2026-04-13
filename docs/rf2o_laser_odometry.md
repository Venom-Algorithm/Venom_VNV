# rf2o_laser_odometry

基于 Range Flow 的 2D 激光扫描里程计，适用于移动机器人平面运动估计。

## 功能

- 从连续 2D 激光扫描中估计平面运动
- 不搜索特征对应，基于扫描梯度进行稠密对齐
- 极低计算开销（单核 0.9ms）
- 适用于底盘里程计不准时的补充定位

## 与系统集成

本项目中 rf2o 作为 Point-LIO 的互补方案：
- **Point-LIO** — 3D 激光惯性里程计，高带宽高频率，用于主定位
- **rf2o** — 2D 激光里程计，轻量快速，用于平面运动场景的辅助定位

两者在 `venom_bringup` 的建图启动文件中统一管理。

## 启动

```bash
# 通过 venom_bringup 统一启动（推荐）
ros2 launch venom_bringup mapping_bringup.launch.py

# 单独启动
ros2 launch rf2o_laser_odometry rf2o_laser_odometry.launch.py
```

## 参考

- 论文：*Planar Odometry from a Radial Laser Scanner. A Range Flow-based Approach.* ICRA 2016
- [rf2o_laser_odometry README](../lio/rf2o_laser_odometry/README.md)
