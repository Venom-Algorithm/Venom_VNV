---
title: Localization
description: Overview of LIO, 2D odometry, relocalization, and map-alignment modules.
---

## Layer Role

The localization layer is responsible for:

1. continuous local pose estimation such as `odom -> base_link`
2. global alignment recovery such as `map -> odom`

## Covered Modules

- [LIO Overview](../lio/index.md)
- [Point-LIO](../lio/point_lio.md)
- [Fast-LIO](../lio/fast_lio.md)
- [rf2o Laser Odometry](rf2o_laser_odometry.md)
- [Relocalization](small_gicp_relocalization.md)

## Structure Inside This Layer

- `localization/lio/`
- `localization/relocalization/`

## Reading Order

1. [LIO Overview](../lio/index.md)
2. [Point-LIO](../lio/point_lio.md)
3. [Relocalization](small_gicp_relocalization.md)
4. [rf2o Laser Odometry](rf2o_laser_odometry.md)
