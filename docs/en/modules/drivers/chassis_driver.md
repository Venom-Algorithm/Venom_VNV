---
title: Chassis Driver Overview
permalink: /en/chassis_driver
desc: Relationship between scout_ros2, hunter_ros2, and ugv_sdk, plus shared interface constraints.
breadcrumb: Drivers
layout: default
---

## Main Components

The current wheeled-platform chain is built from:

- [Scout Driver]({{ '/en/scout_ros2' | relative_url }})
- [Hunter Driver]({{ '/en/hunter_ros2' | relative_url }})
- [UGV SDK]({{ '/en/ugv_sdk' | relative_url }})

## Shared Contract

For Venom VNV, chassis integrations should stay compatible around:

| Direction | Topic / TF | Purpose |
| --- | --- | --- |
| Subscribe | `/cmd_vel` | Velocity commands from upper layers |
| Publish | `/odom` | Odometry output |
| Publish | `odom -> base_link` | Base TF |
| Publish | status topics | Platform-specific feedback |

## Deployment Commonality

No matter whether you use Scout or Hunter, validate the CAN link first, then launch the ROS wrapper.

## Related Pages

- [Chassis CAN Setup]({{ '/en/chassis_can_setup' | relative_url }})
- [Scout Driver]({{ '/en/scout_ros2' | relative_url }})
- [Hunter Driver]({{ '/en/hunter_ros2' | relative_url }})
- [UGV SDK]({{ '/en/ugv_sdk' | relative_url }})
