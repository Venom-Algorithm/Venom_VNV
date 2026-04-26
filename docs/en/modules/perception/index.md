---
title: Perception
description: Overview of image-facing perception modules for detection, tracking,
  and structured target output.
---

## Layer Role

The perception layer turns raw sensor data into structured observations that upper layers can consume directly.

In the current repository, it mainly covers:

- object detection
- QR and barcode recognition
- target tracking
- auto-aim visual front-end logic
- general YOLO-style 2D detections

## Current Directory Mapping

- `driver/ros2_hik_camera`
- `perception/rm_auto_aim`
- `perception/yolo_detector`
- `perception/zbar_ros`

## Current Modules

- [Auto Aim Overview](../auto_aim/index.md)
- [Armor Detection](../auto_aim/armor_detector.md)
- [Target Tracking](../auto_aim/armor_tracker.md)
- [YOLO Detector](yolo_detector.md)
- [ZBar ROS](zbar_ros.md)

## Interface Guidance

New perception modules should preferably follow these rules:

1. reuse standard image-facing inputs such as `/image_raw` and `/camera_info`
2. keep detection, tracking, and control outputs separated
3. do not mix control semantics into pure detector messages
4. generic detectors should stay decoupled from competition-specific task logic

## Module Relationships

- `ros2_hik_camera` provides image and camera-info inputs
- `yolo_detector` provides general 2D detections
- `zbar_ros` provides general QR and barcode recognition results
- `armor_detector` provides armor-specific detection and 3D solving
- `armor_tracker` manages tracked target state
- `auto_aim_solver` turns tracked state into control outputs

## Related Pages

- [Hikrobot Camera Driver](../drivers/ros2_hik_camera.md)
- [Topic Reference](../standards/topics.md)
