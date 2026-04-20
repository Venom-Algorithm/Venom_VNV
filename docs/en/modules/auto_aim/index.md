---
title: Auto Aim Overview
permalink: /en/rm_auto_aim
desc: rm_auto_aim — Armor detection, tracking, ballistics solving, and unified control output.
breadcrumb: Perception
layout: default
---

## Module Group

The current auto-aim chain includes:

- [Armor Detection]({{ '/en/armor_detector' | relative_url }})
- [Target Tracking]({{ '/en/armor_tracker' | relative_url }})
- solver-side logic inside `rm_auto_aim`

## Pipeline

```text
Camera -> detector -> tracker -> solver -> robot output
```

## Focus in This Repository

- consistent input topics from the camera driver
- stable detector and tracker outputs
- unified upper-layer output conventions

## Related Pages

- [Perception]({{ '/en/perception_overview' | relative_url }})
- [YOLO Detector]({{ '/en/yolo_detector' | relative_url }})
