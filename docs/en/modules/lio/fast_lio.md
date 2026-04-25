---
title: Fast-LIO
description: FAST-LIO integration notes and interface constraints inside Venom VNV.
---

## Module Role

`Fast-LIO` is the alternative LIO implementation currently integrated in the repository.

## Focus Inside This Project

The engineering goal is not to make every algorithm identical internally, but to keep the surrounding ROS 2 contract aligned:

- odometry topic naming
- TF naming
- path output
- registered cloud behavior

## Note

The Chinese page remains the detailed source for parameter coverage and repository-specific tuning.
