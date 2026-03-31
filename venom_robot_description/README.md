# venom_robot_description

TF 树发布包，用于定义 Venom 机器人的固定和动态坐标变换关系。

## 功能

- 从 YAML 配置文件读取静态 TF 定义
- 支持从 `/robot_status` 读取角度并发布动态 TF
- 支持不同机器人复用同一套 YAML 结构

## 使用

### 编译
```bash
cd /home/venom/venom_ws
colcon build --packages-select venom_robot_description
source install/setup.bash
```

### 启动
```bash
ros2 launch venom_robot_description scout_mini_description.launch.py
ros2 launch venom_robot_description infantry_description.launch.py
```

### 验证
```bash
# 查看 TF 变换
ros2 run tf2_ros tf2_echo base_link laser_link

# 生成 TF 树图
ros2 run tf2_tools view_frames
```

## 配置

静态 TF 配置示例：

```yaml
transforms:
  - parent_frame: base_link
    child_frame: laser_link
    translation: [0.0, 0.0, 0.2]   # x, y, z (米)
    rotation: [0.0, 0.0, 0.0]      # roll, pitch, yaw (弧度)

动态 TF 配置示例：

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
```

修改后重启 launch 文件即可生效。

## TF 树结构

参见 [docs/tf_tree.md](../docs/tf_tree.md)
