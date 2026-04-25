---
title: Serial Driver
description: venom_serial_driver — Serial communication between the onboard computer
  and the lower-level controller.
---

## Module Role

`venom_serial_driver` is the project-specific serial communication layer between the onboard computer and the lower-level control board.

It is typically used for:

- command delivery
- status feedback
- robot-level control bridging

## Why It Matters

This package is often the final bridge between high-level ROS 2 decisions and custom controller-side execution.

## Related Pages

- [Driver Overview](index.md)
- [Topic Reference](../standards/topics.md)

## Note

The Chinese documentation remains the most complete source for protocol-level details.
