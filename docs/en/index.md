---
title: Venom VNV
description: A general-purpose robotics platform for multi-vehicle systems, navigation,
  manipulation, auto aim, and multi-module coordination.
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

It reduces migration cost between different robot forms by keeping the driver, perception, localization, planning, mission, system, and simulation layers aligned under stable interface conventions.

The repository focuses on reusable engineering capabilities such as:

- Sensors, serial links, chassis platforms, and robot arm integration
- Detection, tracking, targeting, and general object-detection pipelines
- LIO, odometry, and relocalization
- planning-oriented modules for planners, controllers, and manipulation motion generation
- mission-oriented modules for waypoint, BT, monitor, and task progression
- Shared startup conventions across multiple robot types

## Quick Start

<div class="card-grid" data-toc-exclude>
  <a href="home/quick_start/" class="card" style="text-decoration:none">
    <h3>⚙️ Quick Start</h3>
    <p>Clone the workspace, install dependencies, and build the project for the first time.</p>
  </a>
  <a href="deployment/environment/" class="card" style="text-decoration:none">
    <h3>🧰 Environment</h3>
    <p>Prepare Ubuntu, ROS 2, rosdep, VS Code, Clash, and NoMachine.</p>
  </a>
  <a href="deployment/lidar_setup/" class="card" style="text-decoration:none">
    <h3>📡 LiDAR Setup</h3>
    <p>Install Livox-SDK2, configure MID360 networking, and verify the LiDAR link.</p>
  </a>
  <a href="home/launch_usage/" class="card" style="text-decoration:none">
    <h3>🚀 Launch & Use</h3>
    <p>Check common build, rebuild, and launch commands used in daily development.</p>
  </a>
  <a href="deployment/chassis_can_setup/" class="card" style="text-decoration:none">
    <h3>🛞 Chassis CAN</h3>
    <p>Bring up the chassis CAN interface and verify the low-level communication chain.</p>
  </a>
  <a href="deployment/piper_can_setup/" class="card" style="text-decoration:none">
    <h3>🦾 Arm CAN</h3>
    <p>Detect the Piper CAN adapter, name the interface, and start the arm control chain.</p>
  </a>
  <a href="deployment/rc_local/" class="card" style="text-decoration:none">
    <h3>🔁 rc.local</h3>
    <p>Set up boot-time commands and network-priority initialization.</p>
  </a>
  <a href="deployment/run_modes/" class="card" style="text-decoration:none">
    <h3>🧭 Run Modes</h3>
    <p>Understand the typical bringup combinations used for testing and full-system runs.</p>
  </a>
  <a href="deployment/system_overview/" class="card" style="text-decoration:none">
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
    <tr><td>Drivers</td><td><code>driver/venom_px4_bridge</code></td><td>PX4 integration project root containing vendored <code>px4_msgs</code> and the bridge package</td></tr>
    <tr><td>Perception</td><td><code>perception/rm_auto_aim</code></td><td>Auto aim stack including detection, tracking, solving, and interface definitions</td></tr>
    <tr><td>Perception</td><td><code>perception/yolo_detector</code></td><td>General YOLO-based 2D detector with custom message definitions</td></tr>
    <tr><td>Perception</td><td><code>perception/zbar_ros</code></td><td>ZBar-based QR and barcode recognition with structured detection outputs</td></tr>
    <tr><td>Perception</td><td><code>perception/rm_auto_aim/armor_detector</code></td><td>Armor detection module</td></tr>
    <tr><td>Perception</td><td><code>perception/rm_auto_aim/armor_tracker</code></td><td>Target tracking module</td></tr>
    <tr><td>Perception</td><td><code>perception/rm_auto_aim/auto_aim_solver</code></td><td>Ballistics and target solving module</td></tr>
    <tr><td>Perception</td><td><code>perception/rm_auto_aim/auto_aim_interfaces</code></td><td>Message and interface definitions for the auto aim pipeline</td></tr>
    <tr><td>Localization</td><td><code>localization/lio/Point-LIO</code></td><td>High-bandwidth LiDAR-inertial odometry, tuned for MID360 workflows</td></tr>
    <tr><td>Localization</td><td><code>localization/lio/Fast-LIO</code></td><td>ROS 2 version of FAST-LIO</td></tr>
    <tr><td>Localization</td><td><code>localization/lio/rf2o_laser_odometry</code></td><td>2D laser odometry based on range flow</td></tr>
    <tr><td>Localization</td><td><code>localization/relocalization/small_gicp_relocalization</code></td><td>Point-cloud relocalization based on small_gicp</td></tr>
    <tr><td>Planning</td><td><code>planning/navigation/ego-planner-swarm</code></td><td>UAV local planning and swarm-planning submodule tracking the upstream <code>ros2_version</code> branch</td></tr>
    <tr><td>Planning</td><td><code>planning/manipulation</code></td><td>Entry point for manipulation-side motion planning modules, currently kept as a placeholder</td></tr>
    <tr><td>Mission</td><td><code>mission/</code></td><td>Entry point for waypoint, behavior-tree, monitor, and mission-management packages, with placeholder <code>navigation/</code> and <code>manipulation/</code> subfolders already created</td></tr>
    <tr><td>System</td><td><code>venom_bringup</code></td><td>Main system entry for mode composition, robot assembly, and full-stack bringup</td></tr>
    <tr><td>System</td><td><code>venom_robot_description</code></td><td>Robot model, URDF, and TF description package</td></tr>
    <tr><td>Simulation</td><td><code>simulation/venom_nav_simulation</code></td><td>Standalone navigation simulation workspace for MID360, LIO, and Nav2 validation</td></tr>
  </tbody>
</table>

### Documentation Groups

| Group | Description |
|------|------|
| Deployment & Usage | Environment, LiDAR, CAN setup, boot-time config, and run modes |
| Modules & Interfaces | Drivers, perception, localization, planning, mission, system, simulation, and interface conventions |
| Support & Community | FAQ, troubleshooting, migration notes, contact, and contribution guidance |

## Suggested Reading

1. Start from [Quick Start](home/quick_start.md) for the standard workspace flow.
2. Continue with [Environment Setup](deployment/environment.md) and [LiDAR Setup](deployment/lidar_setup.md) for a first deployment.
3. Move to [Modules & Interfaces](modules/index.md) when you need package-level details.
