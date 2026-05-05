---
title: Topics & TF Overview
description: System-level topic map, TF relationships, and key data flow conventions.
---

## Why This Page Exists

When multiple packages are brought together, the first thing that needs to stay stable is not the algorithm itself, but the system contract:

- Which topics are expected
- Which frames are fixed
- Which modules publish `odom`
- Which future module is allowed to own `map -> odom`

## Core System Layers

| Layer | Typical Outputs |
| --- | --- |
| Driver layer | LiDAR, IMU, image, serial, chassis state |
| Localization layer | `/odom`, registered clouds, path, TF |
| Global-localization interface | reserved `map -> odom` contract |
| Task / integration layer | High-level robot behavior and launch orchestration |

The default workspace no longer initializes `small_gicp_relocalization`. Therefore, `map -> odom` is a reserved interface contract, not an active default relocalization node.

## Typical Data Flow

```text
MID360 -> livox_ros_driver2 -> Point-LIO / Fast-LIO -> /odom
Camera -> ros2_hik_camera -> armor_detector -> armor_tracker -> solver
Chassis / arm / controller links -> dedicated drivers -> robot actions
```

## Further Reading

- [Topic Reference](../modules/standards/topics.md)
- [TF Tree](../modules/standards/tf_tree.md)
