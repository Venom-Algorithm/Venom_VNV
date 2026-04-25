---
title: 机器人描述
description: venom_robot_description — TF 树发布包，定义坐标变换关系。
---

## 模块定位

`venom_robot_description` 负责描述机器人本体的坐标系关系，主要包括：

- 静态 TF 的定义与发布
- 与机器人结构相关的固定安装位姿
- 某些依赖状态输入的动态 TF 发布

它不负责定位估计本身，而是为定位、自瞄、传感器驱动提供统一的坐标系骨架。

## 核心职责

- 发布 `base_link` 到各传感器坐标系的静态变换
- 发布与机器人机构相关的动态变换
- 通过 YAML 组织描述信息，方便不同机器人复用

## 当前参数入口

当前动态 TF 发布节点最核心的运行参数只有一个：

- `config_file`

代码入口在：

- [`dynamic_tf_publisher.py`](https://github.com/Venom-Algorithm/Venom_VNV/blob/master/venom_robot_description/venom_robot_description/dynamic_tf_publisher.py)

常用配置文件包括：

- [infantry.yaml](https://github.com/Venom-Algorithm/Venom_VNV/blob/master/venom_robot_description/config/infantry.yaml)
- [scout_mini.yaml](https://github.com/Venom-Algorithm/Venom_VNV/blob/master/venom_robot_description/config/scout_mini.yaml)
- [sentry.yaml](https://github.com/Venom-Algorithm/Venom_VNV/blob/master/venom_robot_description/config/sentry.yaml)

## 参数说明

### 节点参数

| 参数名 | 作用 | 默认值 |
| --- | --- | --- |
| `config_file` | 指向机器人描述 YAML 的路径。没有这个参数时节点不会启动成功。 | `""` |

### 配置文件字段

| 字段名 | 作用 | 说明 |
| --- | --- | --- |
| `robot_status_topic` | 动态 TF 读取机器人状态的话题。 | 通常为 `/robot_status`。 |
| `publish_rate` | 动态 TF 发布频率，单位 Hz。 | 值越高，机构姿态更新越及时。 |
| `static_transforms` | 静态变换列表。 | 用于描述固定安装关系。 |
| `dynamic_transforms` | 动态变换列表。 | 用于描述云台、枪口等会随状态变化的机构。 |
| `parent_frame` | 父坐标系。 | 每条 TF 必填。 |
| `child_frame` | 子坐标系。 | 每条 TF 必填。 |
| `translation` | 平移 `[x, y, z]`，单位米。 | 静态和动态 TF 都可定义。 |
| `rotation` | 固定旋转 `[roll, pitch, yaw]`，单位弧度。 | 动态 TF 会在此基础上叠加实时角度。 |
| `angle_source` | 动态角度读取路径。 | 例如从 `RobotStatus` 中读取 `velocity.angular.z`。 |
| `axis` | 动态旋转叠加轴。 | `x` / `y` / `z`。 |
| `sign` | 动态角度符号修正。 | 机械正方向与软件正方向不一致时使用。 |

## 典型坐标系

- `base_link`
- `laser_link`
- `gimbal_link`
- `barrel_link`
- 其他机器人结构相关 frame

系统级 TF 结构见：

- [TF 树](../standards/tf_tree.md)

## 推荐启动方式

```bash
# Scout Mini 底盘
ros2 launch venom_robot_description scout_mini_description.launch.py

# 步兵平台
ros2 launch venom_robot_description infantry_description.launch.py
```

## 配置方式

通常通过 YAML 定义两类变换：

1. 静态变换

```yaml
transforms:
  - parent_frame: base_link
    child_frame: laser_link
    translation: [0.0, 0.0, 0.2]
    rotation: [0.0, 0.0, 0.0]
```

2. 动态变换

```yaml
dynamic_transforms:
  - parent_frame: base_link
    child_frame: gimbal_yaw_link
    angle_source: velocity.angular.z
    axis: z
```

在当前工程里，更推荐直接看实际配置文件，而不是只看抽象示例，因为不同平台的云台和传感器安装差异很大。

## 调试重点

- 先验证静态 TF 是否完整
- 再检查动态 TF 的角度来源是否正确
- 不要让这里和 LIO 的 `odom -> base_link` 主 TF 职责重叠

如果 TF 看起来“差一点点”，优先检查：

- YAML 里的平移单位是否都是米
- 欧拉角是否按弧度填写
- `sign` 和 `axis` 是否与真实机械方向一致

## 相关页面

- [TF 树](../standards/tf_tree.md)
- [话题参考](../standards/topics.md)
- [venom_serial_driver](../drivers/venom_serial_driver.md)

## 进一步阅读

- [venom_robot_description README](https://github.com/Venom-Algorithm/Venom_VNV/blob/master/venom_robot_description/README.md)
