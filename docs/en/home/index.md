---
title: Venom VNV
permalink: /en/
desc: A general-purpose robotics platform for multi-vehicle systems, navigation, manipulation, auto aim, and system integration.
breadcrumb: Home
layout: default
---

## Project Positioning

Venom VNV is a general-purpose robotics platform built on ROS 2 Humble.

The project aims to provide a reusable system base for:

- Navigation
- Manipulation
- Auto aim
- UGV platforms
- UAV platforms
- USV platforms

It reduces migration cost between different robot forms by keeping the driver layer, localization layer, perception layer, task layer, and interface conventions aligned.

The repository focuses on reusable engineering capabilities such as:

- Sensors, serial links, chassis platforms, and robot arm integration
- LIO, odometry, and relocalization
- Detection, tracking, and targeting pipelines
- Shared startup conventions across multiple robot types

## Quick Start

<div class="card-grid" data-toc-exclude>
  <a href="{{ '/en/quick_start' | relative_url }}" class="card" style="text-decoration:none">
    <h3>⚙️ Quick Start</h3>
    <p>Clone the workspace, install dependencies, and build the project for the first time.</p>
  </a>
  <a href="{{ '/en/environment' | relative_url }}" class="card" style="text-decoration:none">
    <h3>🧰 Environment</h3>
    <p>Prepare Ubuntu, ROS 2, rosdep, VS Code, Clash, and NoMachine.</p>
  </a>
  <a href="{{ '/en/lidar_setup' | relative_url }}" class="card" style="text-decoration:none">
    <h3>📡 LiDAR Setup</h3>
    <p>Install Livox-SDK2, configure MID360 networking, and verify the LiDAR link.</p>
  </a>
  <a href="{{ '/en/launch_usage' | relative_url }}" class="card" style="text-decoration:none">
    <h3>🚀 Launch & Use</h3>
    <p>Check common build, rebuild, and launch commands used in daily development.</p>
  </a>
  <a href="{{ '/en/chassis_can_setup' | relative_url }}" class="card" style="text-decoration:none">
    <h3>🛞 Chassis CAN</h3>
    <p>Bring up the chassis CAN interface and verify the low-level communication chain.</p>
  </a>
  <a href="{{ '/en/piper_can_setup' | relative_url }}" class="card" style="text-decoration:none">
    <h3>🦾 Arm CAN</h3>
    <p>Detect the Piper CAN adapter, name the interface, and start the arm control chain.</p>
  </a>
  <a href="{{ '/en/rc_local' | relative_url }}" class="card" style="text-decoration:none">
    <h3>🔁 rc.local</h3>
    <p>Set up boot-time commands and network-priority initialization.</p>
  </a>
  <a href="{{ '/en/run_modes' | relative_url }}" class="card" style="text-decoration:none">
    <h3>🧭 Run Modes</h3>
    <p>Understand the typical bringup combinations used for testing and full-system runs.</p>
  </a>
  <a href="{{ '/en/system_overview' | relative_url }}" class="card" style="text-decoration:none">
    <h3>🧩 Topics & TF</h3>
    <p>Review the system-level topic contracts and TF conventions.</p>
  </a>
</div>

## Project Overview

The repository includes both built-in packages and external submodules. For a quick overview, the homepage keeps everything in one long table.

<table class="home-overview-table">
  <thead>
    <tr>
      <th>Category</th>
      <th>Path</th>
      <th>Description</th>
    </tr>
  </thead>
  <tbody>
    <tr><td>Drivers</td><td><code>driver/livox_ros_driver2</code></td><td>Livox MID360 driver and point cloud publishing</td></tr>
    <tr><td>Drivers</td><td><code>driver/ros2_hik_camera</code></td><td>Hikrobot USB3 industrial camera driver</td></tr>
    <tr><td>Drivers</td><td><code>driver/venom_serial_driver</code></td><td>NUC-to-controller serial communication driver</td></tr>
    <tr><td>Drivers</td><td><code>driver/scout_ros2</code></td><td>ROS 2 wrapper for Scout / Scout Mini platforms</td></tr>
    <tr><td>Drivers</td><td><code>driver/hunter_ros2</code></td><td>ROS 2 wrapper for Hunter platforms</td></tr>
    <tr><td>Drivers</td><td><code>driver/ugv_sdk</code></td><td>Low-level C++ SDK and CAN tools for AgileX / Weston Robot platforms</td></tr>
    <tr><td>Drivers</td><td><code>driver/piper_ros</code></td><td>Piper arm ROS 2 control, description, MoveIt, and simulation packages</td></tr>
    <tr><td>Localization</td><td><code>lio/Point-LIO</code></td><td>High-bandwidth LiDAR-inertial odometry, tuned for MID360 workflows</td></tr>
    <tr><td>Localization</td><td><code>lio/Fast-LIO</code></td><td>ROS 2 version of FAST-LIO</td></tr>
    <tr><td>Localization</td><td><code>lio/rf2o_laser_odometry</code></td><td>2D laser odometry based on range flow</td></tr>
    <tr><td>Relocalization</td><td><code>relocalization/small_gicp_relocalization</code></td><td>Point-cloud relocalization based on small_gicp</td></tr>
    <tr><td>Auto Aim</td><td><code>rm_auto_aim</code></td><td>Auto aim stack including detection, tracking, solving, and interface definitions</td></tr>
    <tr><td>Auto Aim</td><td><code>rm_auto_aim/armor_detector</code></td><td>Armor detection module</td></tr>
    <tr><td>Auto Aim</td><td><code>rm_auto_aim/armor_tracker</code></td><td>Target tracking module</td></tr>
    <tr><td>Auto Aim</td><td><code>rm_auto_aim/auto_aim_solver</code></td><td>Ballistics and target solving module</td></tr>
    <tr><td>Auto Aim</td><td><code>rm_auto_aim/auto_aim_interfaces</code></td><td>Message and interface definitions for the auto aim pipeline</td></tr>
    <tr><td>Integration</td><td><code>venom_bringup</code></td><td>Main bringup entry with example, infantry, sentry, scout_mini, and hunter_se configs</td></tr>
    <tr><td>Integration</td><td><code>venom_robot_description</code></td><td>Robot model, URDF, and TF description package</td></tr>
  </tbody>
</table>

### Documentation Groups

| Group | Description |
|------|------|
| Deployment & Usage | Environment, LiDAR, CAN setup, boot-time config, and run modes |
| Modules & Interfaces | Drivers, LIO, localization, auto aim, integration, and interface conventions |
| Support & Community | FAQ, troubleshooting, migration notes, contact, and contribution guidance |

## Suggested Reading

1. Start from [Quick Start]({{ '/en/quick_start' | relative_url }}) for the standard workspace flow.
2. Continue with [Environment Setup]({{ '/en/environment' | relative_url }}) and [LiDAR Setup]({{ '/en/lidar_setup' | relative_url }}) for a first deployment.
3. Move to [Modules & Interfaces]({{ '/en/interface_reference' | relative_url }}) when you need package-level details.
