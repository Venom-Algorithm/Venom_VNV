---
title: Topics & TF Overview
permalink: /en/system_overview
desc: System-level topic map, TF relationships, and key data flow conventions.
breadcrumb: Deployment & Usage
layout: default
---

## Why This Page Exists

When multiple packages are brought together, the first thing that needs to stay stable is not the algorithm itself, but the system contract:

- Which topics are expected
- Which frames are fixed
- Which modules publish `odom`
- Which module is responsible for `map -> odom`

## Core System Layers

| Layer | Typical Outputs |
| --- | --- |
| Driver layer | LiDAR, IMU, image, serial, chassis state |
| Localization layer | `/odom`, registered clouds, path, TF |
| Relocalization layer | `map -> odom` |
| Task / integration layer | High-level robot behavior and launch orchestration |

## Typical Data Flow

```text
MID360 -> livox_ros_driver2 -> Point-LIO / Fast-LIO -> /odom
Camera -> ros2_hik_camera -> armor_detector -> armor_tracker -> solver
Chassis / arm / controller links -> dedicated drivers -> robot actions
```

## Further Reading

- [Topic Reference]({{ '/en/topics' | relative_url }})
- [TF Tree]({{ '/en/tf_tree' | relative_url }})
