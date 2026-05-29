---
title: Localization
description: Overview of LIO, 2D odometry, and future global-localization interfaces.
---

## Layer Role

The localization layer is responsible for:

1. continuous local pose estimation such as `odom -> base_link`
2. keeping a stable `map -> odom` interface contract for future global-localization / relocalization modules

## Covered Modules

- [LIO Overview](../lio/index.md)
- [Point-LIO](../lio/point_lio.md)
- [Fast-LIO](../lio/fast_lio.md)
- [rf2o Laser Odometry](rf2o_laser_odometry.md)

The GICP relocalization submodule is temporarily disabled because of known stability issues and is no longer initialized as a main-repository submodule.

## Structure Inside This Layer

- `localization/lio/`
- `localization/relocalization/` reserved for future global-localization / relocalization modules

## Reading Order

1. [LIO Overview](../lio/index.md)
2. [Point-LIO](../lio/point_lio.md)
3. [rf2o Laser Odometry](rf2o_laser_odometry.md)
