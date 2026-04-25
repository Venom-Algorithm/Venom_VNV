---
title: Hunter Driver
description: hunter_ros2 — ROS 2 wrapper for AgileX Hunter platforms.
---

## Module Role

`hunter_ros2` is the ROS 2 wrapper for Hunter-family chassis. It:

- consumes `/cmd_vel`
- communicates with the base through `ugv_sdk`
- publishes odometry and Hunter status feedback
- keeps the `odom -> base_link` contract stable for the rest of the stack

## Main Interfaces

| Direction | Topic / TF | Type | Description |
| --- | --- | --- | --- |
| Subscribe | `/cmd_vel` | `geometry_msgs/Twist` | velocity command |
| Publish | `/odom` | `nav_msgs/Odometry` | odometry |
| Publish | `/hunter_status` | `hunter_msgs/HunterStatus` | chassis state |
| Publish | `odom -> base_link` | `tf2` | base TF |

## Typical Launch

```bash
ros2 launch hunter_base hunter_base.launch.py
```

## Related Pages

- [Chassis Driver Overview](chassis_driver.md)
- [UGV SDK](ugv_sdk.md)
- [Chassis CAN Setup](../../deployment/chassis_can_setup.md)
