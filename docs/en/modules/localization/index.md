---
title: Localization
permalink: /en/localization_overview
desc: Overview of 3D odometry, 2D odometry, and global relocalization modules.
breadcrumb: Modules & Interfaces
layout: default
---

## Covered Modules

- [rf2o Laser Odometry]({{ '/en/rf2o_laser_odometry' | relative_url }})
- [Relocalization]({{ '/en/small_gicp_relocalization' | relative_url }})

## System Role

This section complements the LIO section:

- LIO handles the main 3D odometry chain
- 2D odometry can serve as a lighter-weight supplement
- relocalization is responsible for `map -> odom`
