---
title: Target Tracking
permalink: /en/armor_tracker
desc: armor_tracker — EKF-based multi-target tracking with motion prediction and compensation.
breadcrumb: Auto Aim
layout: default
---

## Module Role

`armor_tracker` consumes detection output and maintains a stable target state for the solver stage.

## Focus

- filtering noisy detections
- preserving stable target identity
- providing predicted target state for the solver

## Note

The Chinese page remains the detailed source for the full tracking parameter set.
