---
title: Topic Reference
description: System-level ROS 2 topics, data flow, and important interface fields.
---

## Goal

This page is the topic-level contract for the system. It helps answer:

- which topics exist
- which package owns them
- which frame IDs are expected

## Typical Categories

- driver outputs
- localization outputs
- reserved global-localization / relocalization interfaces
- auto-aim pipeline topics
- integration-level topics

Current default LIO modules publish `/odom`, `/cloud_registered`, `/cloud_registered_body`, `/map_cloud`, and `/path`. The previous GICP relocalization stack is disabled, so no relocalization topic should be assumed to exist in a fresh workspace.

## Note

The Chinese page remains the detailed source for the complete tables and field notes.
