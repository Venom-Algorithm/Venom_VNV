---
title: LIO
description: Overall constraints, interface conventions, and algorithm entry points
  for LiDAR-inertial odometry.
---

## Scope Inside The Localization Layer

This section covers the LiDAR-inertial odometry modules currently used in the repository:

- [Point-LIO](point_lio.md)
- [Fast-LIO](fast_lio.md)

## Shared Conventions

The repository aims to keep the following stable across LIO implementations:

- a consistent odometry topic
- stable TF responsibility around `odom -> base_link`
- consistent naming for registered clouds and path output

## Related Pages

- [Localization](../localization/index.md)
- [Topic Reference](../standards/topics.md)
- [TF Tree](../standards/tf_tree.md)
