---
title: LIO
permalink: /en/lio_overview
desc: Overall constraints, interface conventions, and algorithm entry points for LiDAR-inertial odometry.
breadcrumb: Modules & Interfaces
layout: default
---

## Scope

This section covers the LiDAR-inertial odometry modules currently used in the repository:

- [Point-LIO]({{ '/en/point_lio' | relative_url }})
- [Fast-LIO]({{ '/en/fast_lio' | relative_url }})

## Shared Conventions

The repository aims to keep the following stable across LIO implementations:

- a consistent odometry topic
- stable TF responsibility around `odom -> base_link`
- consistent naming for registered clouds and path output

## Related Pages

- [Topic Reference]({{ '/en/topics' | relative_url }})
- [TF Tree]({{ '/en/tf_tree' | relative_url }})
