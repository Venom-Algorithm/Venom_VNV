---
title: TF Tree
permalink: /en/tf_tree
desc: System-level frame hierarchy and frame-role conventions.
breadcrumb: Quick Start
layout: default
---

## Goal

This page records the expected frame hierarchy used across the robot stack.

## Core Idea

Even when algorithms are swapped, the surrounding TF responsibilities should stay stable:

- `odom -> base_link` from odometry
- `map -> odom` from relocalization or global localization
- sensor frames and static robot-description frames from the description layer

## Note

The Chinese page remains the detailed source for the complete TF notes.
