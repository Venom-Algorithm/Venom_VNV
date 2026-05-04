---
title: Relocalization (Temporarily Disabled)
description: The GICP relocalization module is temporarily removed from the main-repository submodules because of known stability issues.
---

## Current Status

`small_gicp_relocalization` is temporarily disabled and is no longer initialized as a `Venom_VNV` main-repository submodule.

This means:

- `.gitmodules` no longer contains `localization/relocalization/small_gicp_relocalization`
- `make submodules-ugv` no longer initializes this repository
- fresh workspaces do not contain the `small_gicp_relocalization` package by default
- existing relocalization launch files under `venom_bringup` are kept as historical integration points, but they are not recommended for current use

## Conditions Before Re-Enabling

Before bringing this module back, we should first:

1. define clear ownership for the `map -> odom` transform so it does not conflict with LIO or Nav2
2. add safe fallback behavior for missing prior maps, input clouds, initial poses, and TF lookups
3. add bag-based regression tests for low-speed motion, high-speed rotation, and localization jumps
4. verify that missing RViz, slow disks, empty clouds, and TF timeouts do not block the main localization path

## Current Alternative

For Mid360 + Point-LIO validation, prefer the LIO odometry output itself and do not rely on GICP relocalization correction.
