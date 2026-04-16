---
title: Hikrobot Camera Driver
permalink: /en/ros2_hik_camera
desc: ros2_hik_camera — ROS 2 driver for Hikrobot USB3 industrial cameras.
breadcrumb: Drivers
layout: default
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

- [Auto Aim Overview]({{ '/en/rm_auto_aim' | relative_url }})
- [Armor Detection]({{ '/en/armor_detector' | relative_url }})
- [Topic Reference]({{ '/en/topics' | relative_url }})

## Note

The Chinese page remains the more detailed reference for parameter tuning.
