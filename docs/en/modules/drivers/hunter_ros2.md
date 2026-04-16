---
title: Hunter Driver
permalink: /en/hunter_ros2
desc: hunter_ros2 — ROS 2 wrapper for AgileX Hunter platforms.
breadcrumb: Drivers
layout: default
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

- [Chassis Driver Overview]({{ '/en/chassis_driver' | relative_url }})
- [UGV SDK]({{ '/en/ugv_sdk' | relative_url }})
- [Chassis CAN Setup]({{ '/en/chassis_can_setup' | relative_url }})
