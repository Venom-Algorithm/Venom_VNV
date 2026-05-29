---
title: TF Tree
description: System-level frame hierarchy and frame-role conventions.
---

## Goal

This page records the expected frame hierarchy used across the robot stack.

## Core Idea

Even when algorithms are swapped, the surrounding TF responsibilities should stay stable:

- `odom -> base_link` from odometry
- `map -> odom` reserved for a future relocalization or global-localization module
- sensor frames and static robot-description frames from the description layer

The default workspace currently does not initialize `small_gicp_relocalization`, so `map -> odom` is a reserved contract instead of an active default publisher.

## Note

The Chinese page remains the detailed source for the complete TF notes.
