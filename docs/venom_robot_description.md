# venom_robot_description

TF 树发布包，定义 Venom 机器人的固定和动态坐标变换关系。

## 功能

- 从 YAML 配置文件读取静态 TF 定义
- 支持从 `/robot_status` 读取角度并发布动态 TF
- 支持不同机器人复用同一套 YAML 结构

## 快速开始

```bash
# Scout Mini 底盘
ros2 launch venom_robot_description scout_mini_description.launch.py

# 步兵
ros2 launch venom_robot_description infantry_description.launch.py
```

## 验证

```bash
# 查看 TF 变换
ros2 run tf2_ros tf2_echo base_link laser_link

# 生成 TF 树图
ros2 run tf2_tools view_frames
```

## 配置

静态 TF 示例：

```yaml
transforms:
  - parent_frame: base_link
    child_frame: laser_link
    translation: [0.0, 0.0, 0.2]   # x, y, z (米)
    rotation: [0.0, 0.0, 0.0]      # roll, pitch, yaw (弧度)
```

动态 TF 示例（云台跟随 C 板角度）：

```yaml
robot_status_topic: /robot_status
publish_rate: 50.0

dynamic_transforms:
  - parent_frame: base_link
    child_frame: gimbal_yaw_link
    translation: [0.0, 0.0, 0.36]
    rotation: [0.0, 0.0, 0.0]
    angle_source: velocity.angular.z
    axis: z
```

## TF 树结构

详见 [docs/tf_tree.md](tf_tree.md)

## 详细文档

详见：[venom_robot_description README](../venom_robot_description/README.md)
