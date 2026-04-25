---
title: Hikrobot Camera Driver
description: ros2_hik_camera — ROS 2 driver for Hikrobot USB3 industrial cameras.
---

## Module Role

`ros2_hik_camera` is the image-input driver used by the auto-aim chain. It:

- initializes the industrial camera
- captures images
- publishes ROS 2 image and camera-info messages
- provides the image source for the detector pipeline

## Main Outputs

| Direction | Topic | Type | Description |
| --- | --- | --- | --- |
| Publish | `/image_raw` | `sensor_msgs/Image` | raw image stream |
| Publish | `/camera_info` | `sensor_msgs/CameraInfo` | calibration and camera model |

## Common Configs

- `config/camera_params.yaml`
- `config/camera_info.yaml`

## Related Pages

- [Auto Aim Overview](../auto_aim/index.md)
- [Armor Detection](../auto_aim/armor_detector.md)
- [Topic Reference](../standards/topics.md)

## Note

The Chinese page remains the more detailed reference for parameter tuning.
