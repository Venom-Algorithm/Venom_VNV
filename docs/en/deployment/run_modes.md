---
title: Run Modes
description: Typical bringup combinations and when each mode should be used.
---

## Purpose

The repository is not used in just one runtime shape. Depending on hardware availability and the current task, you may only want:

- A single driver validation flow
- A localization-only flow
- An auto aim test flow
- A mapping or relocalization flow
- A full system bringup

## Common Patterns

| Mode | Focus |
| --- | --- |
| Driver validation | Check LiDAR, camera, CAN, or serial links separately |
| Localization test | Run MID360 + Point-LIO / Fast-LIO without the rest of the stack |
| Auto aim test | Focus on camera, detector, tracker, and solver |
| Mapping | Validate localization and mapping outputs |
| Relocalization | Validate global localization against an existing map |
| Full robot bringup | Start the integrated stack through `venom_bringup` |

## Recommendation

For day-to-day work, do not jump into a full bringup first. A safer order is:

1. Validate drivers
2. Validate localization
3. Validate task-specific modules
4. Move to integrated bringup last

## Related Pages

- [Launch & Use](../home/launch_usage.md)
- [System Bringup](../modules/integration/venom_bringup.md)
