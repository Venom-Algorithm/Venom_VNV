# grasp_target_fusion

第一波实现提供三部分能力：

- `Detection2D + D435i aligned depth + camera_info + TF` 融合为标准 `GraspTarget`
- `/perception/target_valid` 有效目标信号
- `hand_frame -> camera_link` 静态外参加载框架

## 当前输入接口

- 检测输入：`/perception/detections_2d`
- 检测数组输入：`/perception/detections_2d_array`
- 深度输入：`/camera/camera/aligned_depth_to_color/image_raw`
- 内参输入：`/camera/camera/color/camera_info`
- 相机 frame 默认：`camera_color_optical_frame`

> 以上 D435i 话题和 frame 名称基于本地 `realsense2_camera` 包与现有 launch 核实后填写。

## 当前输出接口

- 抓取目标：`/perception/grasp_target`
- 有效信号：`/perception/target_valid`

## 无 YOLO 时的联调方式

可以先启动一个假的 2D 检测发布器：

```bash
ros2 run grasp_target_fusion fake_detection_publisher
```

默认它会持续往 `/perception/detections_2d` 发布一个中心位于 `320,240` 的小方块检测框。
同时也会往 `/perception/detections_2d_array` 发布只包含这一个检测框的数组消息。

这样可以直接验证：

- `Detection2D -> GraspTarget`
- `/perception/target_valid`
- `pick_place_server` 读取最新视觉目标

## 单目标约束

第一波的 `require_single_target=true` 现在已经在融合节点里生效：

- 如果检测数组里恰好只有 1 个目标，则继续生成 `GraspTarget`
- 如果是 0 个目标或多于 1 个目标，则 `/perception/target_valid` 会变为 `false`

如果上游暂时只有单条 `/perception/detections_2d`，融合节点仍可兼容，但严格的“单目标/多目标”判断需要同时提供检测数组输入。

## 当前限制

- 只支持单个小方块目标
- 不做多目标排序
- 不估计视觉 yaw，默认 `has_yaw=false`
- 现已提供基于棋盘格的 eye-in-hand 采样与求解工具

## 手眼标定入口

- `ros2 run grasp_target_fusion handeye_sample_collector`
- `ros2 run grasp_target_fusion handeye_solver`
