---
title: System Bringup
permalink: /en/venom_bringup
desc: venom_bringup — System launch composition and task-control framework.
breadcrumb: System Integration
layout: default
---

## Module Role

`venom_bringup` is the repository-level integration entry. It is responsible for:

- launch composition
- mode selection
- task-control entry points
- robot-level configuration dispatch

## Common Launch Entries

- `camera.launch.py`
- `examples/mid360_rviz.launch.py`
- `examples/mid360_point_lio.launch.py`
- `scout_mini/scout_mini_mapping.launch.py`
- `relocalization_bringup.launch.py`
- `robot_bringup.launch.py`

## Related Pages

- [Launch & Use]({{ '/en/launch_usage' | relative_url }})
- [Run Modes]({{ '/en/run_modes' | relative_url }})

## Note

The Chinese page remains the more detailed source for configuration and task-controller notes.
