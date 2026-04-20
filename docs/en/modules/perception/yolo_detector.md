---
title: YOLO Detector
permalink: /en/yolo_detector
desc: yolo_detector — General YOLO-based 2D detection module and message set.
breadcrumb: Perception
layout: default
---

## Module Role

`perception/yolo_detector` is a general 2D detection module set. It is not tied to the auto-aim pipeline itself.

It currently contains:

- `yolo_interfaces/`: detection message definitions
- `yolo_detector/`: Python detector node

## Topics

Default topics:

| Direction | Topic | Description |
| --- | --- | --- |
| subscribe | `/image_raw` | input image |
| publish | `/perception/detections` | one-frame detection output |
| publish | `/perception/debug/yolo_result` | debug image |

## Message Scope

The current messages are intentionally minimal and focused on pure 2D detection:

- `YoloBox.msg`
- `YoloHypothesis.msg`
- `YoloDetection.msg`
- `YoloDetections.msg`

They do not carry:

- depth
- 3D pose
- tracker state

If those are needed later, they should be added as separate interfaces instead of overloading this minimal set.

## Current Entry Points

- [yolo_detector.yaml](/Users/liyh/venom_vnv/perception/yolo_detector/config/yolo_detector.yaml)
- [`yolo_node.py`](/Users/liyh/venom_vnv/perception/yolo_detector/yolo_detector/yolo_node.py)

## Run

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch yolo_detector yolo_detector.launch.py model_path:=/path/to/model.pt
```

Or:

```bash
cd ~/venom_ws
source install/setup.bash
ros2 run yolo_detector yolo_node
```

## Relation To Auto Aim

- `yolo_detector` is a general detector
- `rm_auto_aim` is a task-specific visual and control pipeline

They should not be treated as the same module category.

## Related Pages

- [Perception]({{ '/en/perception_overview' | relative_url }})
- [Auto Aim Overview]({{ '/en/rm_auto_aim' | relative_url }})
- [Hikrobot Camera Driver]({{ '/en/ros2_hik_camera' | relative_url }})
