---
title: Auto Aim Overview
description: rm_auto_aim — Armor detection, tracking, ballistics solving, and unified
  control output.
---

## Module Group

The current auto-aim chain includes:

- [Armor Detection](armor_detector.md)
- [Target Tracking](armor_tracker.md)
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

- [Perception](../perception/index.md)
- [YOLO Detector](../perception/yolo_detector.md)
