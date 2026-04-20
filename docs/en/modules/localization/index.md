---
title: Localization
permalink: /en/localization_overview
desc: Overview of LIO, 2D odometry, relocalization, and map-alignment modules.
breadcrumb: Modules & Interfaces
layout: default
---

## Layer Role

The localization layer is responsible for:

1. continuous local pose estimation such as `odom -> base_link`
2. global alignment recovery such as `map -> odom`

## Covered Modules

- [LIO Overview]({{ '/en/lio_overview' | relative_url }})
- [Point-LIO]({{ '/en/point_lio' | relative_url }})
- [Fast-LIO]({{ '/en/fast_lio' | relative_url }})
- [rf2o Laser Odometry]({{ '/en/rf2o_laser_odometry' | relative_url }})
- [Relocalization]({{ '/en/small_gicp_relocalization' | relative_url }})

## Structure Inside This Layer

- `localization/lio/`
- `localization/relocalization/`

## Reading Order

1. [LIO Overview]({{ '/en/lio_overview' | relative_url }})
2. [Point-LIO]({{ '/en/point_lio' | relative_url }})
3. [Relocalization]({{ '/en/small_gicp_relocalization' | relative_url }})
4. [rf2o Laser Odometry]({{ '/en/rf2o_laser_odometry' | relative_url }})
