---
title: Piper Arm Driver
description: piper_ros — ROS 2 control, description, and simulation packages for the
  AgileX Piper arm.
---

## Module Role

`piper_ros` is the ROS 2 package group for the Piper robotic arm. It:

- controls the arm through CAN
- publishes joint states, end pose, and arm status
- provides URDF, MoveIt, and simulation content
- serves as the execution-side interface for manipulation tasks

## Main Subpackages

- `piper`
- `piper_msgs`
- `piper_description`
- `piper_moveit`
- `piper_sim`
- `piper_humble`

## Main Interfaces

| Direction | Topic / Service | Type | Description |
| --- | --- | --- | --- |
| Subscribe | `joint_ctrl_single` | `sensor_msgs/JointState` | joint control input |
| Subscribe | `pos_cmd` | `piper_msgs/PosCmd` | end-effector command |
| Subscribe | `enable_flag` | `std_msgs/Bool` | enable control |
| Publish | `joint_states_single` | `sensor_msgs/JointState` | current joint states |
| Publish | `arm_status` | `piper_msgs/PiperStatusMsg` | arm state |
| Publish | `end_pose` | `geometry_msgs/Pose` | end-effector pose |

## Typical Launches

```bash
ros2 launch piper start_single_piper.launch.py
ros2 launch piper start_single_piper_rviz.launch.py
```

## Related Pages

- [Arm CAN Setup](../../deployment/piper_can_setup.md)
- [System Bringup](../integration/venom_bringup.md)
- [Topic Reference](../standards/topics.md)
