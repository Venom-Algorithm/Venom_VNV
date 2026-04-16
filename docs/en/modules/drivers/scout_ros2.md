---
title: Scout Driver
permalink: /en/scout_ros2
desc: scout_ros2 — ROS 2 wrapper for AgileX Scout and Scout Mini platforms.
breadcrumb: Drivers
layout: default
---

## Module Role

`scout_ros2` is the ROS 2 wrapper for Scout-family chassis. It:

- receives `/cmd_vel`
- talks to the platform through `ugv_sdk`
- publishes odometry, state, and RC status
- exposes the common `odom -> base_link` TF contract

## Main Interfaces

| Direction | Topic / TF | Type | Description |
| --- | --- | --- | --- |
| Subscribe | `/cmd_vel` | `geometry_msgs/Twist` | velocity command |
| Subscribe | `/light_control` | `scout_msgs/ScoutLightCmd` | light control |
| Publish | `/odom` | `nav_msgs/Odometry` | odometry |
| Publish | `/scout_status` | `scout_msgs/ScoutStatus` | chassis state |
| Publish | `/rc_status` | `scout_msgs/ScoutRCState` | remote-controller state |
| Publish | `odom -> base_link` | `tf2` | base TF |

## Typical Launches

```bash
ros2 launch scout_base scout_base.launch.py
ros2 launch scout_base scout_mini_base.launch.py
ros2 launch scout_base scout_mini_omni_base.launch.py
```

## Related Pages

- [Chassis Driver Overview]({{ '/en/chassis_driver' | relative_url }})
- [UGV SDK]({{ '/en/ugv_sdk' | relative_url }})
- [Chassis CAN Setup]({{ '/en/chassis_can_setup' | relative_url }})
