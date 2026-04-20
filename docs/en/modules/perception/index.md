---
title: Perception
permalink: /en/perception_overview
desc: Overview of image-facing perception modules for detection, tracking, and structured target output.
breadcrumb: Modules & Interfaces
layout: default
---

## Layer Role

The perception layer turns raw sensor data into structured observations that upper layers can consume directly.

In the current repository, it mainly covers:

- object detection
- target tracking
- auto-aim visual front-end logic
- general YOLO-style 2D detections

## Current Directory Mapping

- `driver/ros2_hik_camera`
- `perception/rm_auto_aim`
- `perception/yolo_detector`

## Current Modules

- [Auto Aim Overview]({{ '/en/rm_auto_aim' | relative_url }})
- [Armor Detection]({{ '/en/armor_detector' | relative_url }})
- [Target Tracking]({{ '/en/armor_tracker' | relative_url }})
- [YOLO Detector]({{ '/en/yolo_detector' | relative_url }})

## Interface Guidance

New perception modules should preferably follow these rules:

1. reuse standard image-facing inputs such as `/image_raw` and `/camera_info`
2. keep detection, tracking, and control outputs separated
3. do not mix control semantics into pure detector messages
4. generic detectors should stay decoupled from competition-specific task logic

## Related Pages

- [Hikrobot Camera Driver]({{ '/en/ros2_hik_camera' | relative_url }})
- [Topic Reference]({{ '/en/topics' | relative_url }})
