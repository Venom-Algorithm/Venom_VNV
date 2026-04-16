---
title: Livox LiDAR Driver
permalink: /en/livox_ros_driver2
desc: livox_ros_driver2 — Livox MID360 LiDAR driver.
breadcrumb: Drivers
layout: default
---

## Module Role

`livox_ros_driver2` is the official MID360-facing driver layer. It is responsible for:

- establishing network communication with the LiDAR
- receiving and decoding raw device data
- publishing point cloud and IMU messages to ROS 2
- feeding upper-layer modules such as Point-LIO and Fast-LIO

## Main Outputs

| Direction | Topic | Type | Description |
| --- | --- | --- | --- |
| Publish | `/livox/lidar` | `livox_ros_driver2/CustomMsg` or `sensor_msgs/PointCloud2` | LiDAR point cloud |
| Publish | `/livox/imu` | `sensor_msgs/Imu` | Built-in IMU output |

## Key Configs

- `config/MID360_config.json`
- launch parameters such as `xfer_format`, `publish_freq`, and `frame_id`

## Recommended Reading

- [LiDAR Setup]({{ '/en/lidar_setup' | relative_url }})
- [Point-LIO]({{ '/en/point_lio' | relative_url }})
- [Fast-LIO]({{ '/en/fast_lio' | relative_url }})

## Note

The Chinese page remains the more detailed reference for the full parameter coverage.
