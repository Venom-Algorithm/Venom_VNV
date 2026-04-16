---
title: Point-LIO
permalink: /en/point_lio
desc: Point-LIO integration notes, MID360-facing behavior, and repository-specific interface conventions.
breadcrumb: Localization
layout: default
---

## Module Role

`Point-LIO` is currently one of the main 3D LiDAR-inertial odometry implementations used in the repository.

## What This Repository Cares About Most

- fixed TF conventions
- stable odometry output
- consistent registered cloud topics
- repository-specific parameter behavior for MID360 workflows

## In This Repository

The local fork has already been adjusted around:

- mapping defaults
- map publication behavior
- runtime stability fixes
- deployment-oriented parameter exposure

## Note

The Chinese page remains the detailed reference for parameter-by-parameter explanations.
