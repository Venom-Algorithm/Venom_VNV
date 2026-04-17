---
title: 装甲板检测
permalink: /armor_detector
desc: armor_detector — 基于深度学习识别装甲板并解算 3D 位置。
breadcrumb: 自瞄算法
layout: default
---

## 模块定位

`armor_detector` 是自瞄链路中的前端感知模块，负责：

- 订阅相机图像与相机内参
- 识别当前画面中的装甲板目标
- 输出装甲板 2D 检测结果与 3D 位姿解算结果
- 为后续 `armor_tracker` 提供稳定的观测输入

在整套链路中的位置为：

`/image_raw -> armor_detector -> /detector/armors -> armor_tracker`

## 输入与输出

| 方向 | 话题 | 消息类型 | 说明 |
| --- | --- | --- | --- |
| 订阅 | `/image_raw` | `sensor_msgs/Image` | 原始图像输入 |
| 订阅 | `/camera_info` | `sensor_msgs/CameraInfo` | 相机内参与畸变参数 |
| 发布 | `/detector/armors` | `auto_aim_interfaces/Armors` | 装甲板检测结果与解算后的目标信息 |

## 核心职责

- 目标检测：在图像中找到候选装甲板
- 类别区分：区分大小装甲板或编号类别
- 几何解算：结合相机内参做 PnP，恢复目标在相机坐标系下的位置
- 观测标准化：将检测结果整理成后续跟踪器可以直接消费的统一消息

## 参数说明

当前默认参数文件：

- [armor_detector.yaml](/Users/liyh/venom_vnv/perception/rm_auto_aim/armor_detector/config/armor_detector.yaml)

实战常用覆盖入口：

- [infantry/node_params.yaml](/Users/liyh/venom_vnv/venom_bringup/config/infantry/node_params.yaml)
- [sentry/node_params.yaml](/Users/liyh/venom_vnv/venom_bringup/config/sentry/node_params.yaml)

| 参数名 | 作用 | 默认值 |
| --- | --- | --- |
| `debug` | 是否发布调试图像和调试消息。 | `true` |
| `debug_publish_rate` | 调试信息发布频率，单位 Hz。`0` 表示每帧都发。 | `10.0` |
| `camera_info_topic` | 相机内参输入话题。 | `"/camera_info"` |
| `image_topic` | 图像输入话题。 | `"/image_raw"` |
| `armors_topic` | 装甲板检测结果输出话题。 | `"/detector/armors"` |
| `marker_topic` | RViz Marker 输出话题。 | `"/detector/marker"` |
| `debug_lights_topic` | 灯条调试话题。 | `"/detector/debug_lights"` |
| `debug_armors_topic` | 装甲板调试话题。 | `"/detector/debug_armors"` |
| `debug_binary_img_topic` | 二值图调试话题。 | `"/detector/binary_img"` |
| `debug_number_img_topic` | 数字 ROI 调试图话题。 | `"/detector/number_img"` |
| `debug_result_img_topic` | 检测结果叠加图话题。 | `"/detector/result_img"` |
| `detect_color` | 敌方颜色选择。`0=RED`，`1=BLUE`。 | `0` |
| `binary_thres` | 二值化阈值。值越大越保守，过大可能漏检暗目标。 | `150` |
| `classifier_threshold` | 数字分类置信度阈值。值越大越严格，误检会少但漏检会增多。 | `0.6` |
| `ignore_classes` | 分类结果忽略名单。命中的类别会直接被过滤。 | `["negative"]` |
| `light.min_ratio` | 灯条最小宽高比。过小会接纳过细噪声。 | `0.05` |
| `light.max_ratio` | 灯条最大宽高比。过大则容易把非灯条结构误认为灯条。 | `0.4` |
| `light.max_angle` | 单灯条允许的最大倾斜角，单位度。 | `40.0` |
| `armor.min_light_ratio` | 一对灯条长度比下限。越大越要求左右灯条长度接近。 | `0.6` |
| `armor.min_small_center_distance` | 小装甲中心距下限，按灯条长度归一化。 | `0.8` |
| `armor.max_small_center_distance` | 小装甲中心距上限，按灯条长度归一化。 | `3.2` |
| `armor.min_large_center_distance` | 大装甲中心距下限，按灯条长度归一化。 | `3.2` |
| `armor.max_large_center_distance` | 大装甲中心距上限，按灯条长度归一化。 | `5.5` |
| `armor.max_angle` | 成对灯条连线允许的最大倾斜角，单位度。 | `35.0` |

## 推荐启动方式

通常不单独启动，建议由上层统一托管：

```bash
# 步兵自瞄链路（推荐）
ros2 launch venom_bringup infantry_auto_aim.launch.py
```

如需单独调试：

```bash
ros2 launch armor_detector armor_detector.launch.py
```

## 调试重点

- 如果完全没有检测结果，先检查 `/image_raw` 与 `/camera_info` 是否正常发布
- 如果 2D 框正常但 3D 位置异常，优先检查相机内参与装甲板尺寸配置
- 如果结果抖动较大，通常要和 `armor_tracker` 一起联调，不建议只看单帧检测效果

常见调参顺序：

- 完全看不到目标：先查 `detect_color`、`binary_thres`
- 灯条误检多：再收紧 `light.*`
- 成对误配多：再收紧 `armor.*`
- 数字分类容易错：再调 `classifier_threshold` 和 `ignore_classes`

## 相关页面

- [自瞄算法总览]({{ '/rm_auto_aim' | relative_url }})
- [目标跟踪]({{ '/armor_tracker' | relative_url }})
- [话题参考]({{ '/topics' | relative_url }})

## 进一步阅读

- [armor_detector README](../../../perception/rm_auto_aim/armor_detector/README.md)
