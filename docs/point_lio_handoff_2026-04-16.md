# Point-LIO Handoff Context

Date: 2026-04-16
Workspace: `~/venom_ws/src/venom_vnv`
Primary package: `~/venom_ws/src/venom_vnv/localization/lio/Point-LIO`
Primary bringup: `~/venom_ws/src/venom_vnv/venom_bringup`

## User Goal

The user wants to investigate and improve Point-LIO performance, especially drift during high-speed rotation and high-speed motion, and then run controlled tests using recorded raw Mid360 bags.

## Repository / Branch Context

- Current Point-LIO remote setup:
  - `origin`: `git@github.com:Venom-Algorithm/Point-LIO.git`
  - `upstream`: `https://github.com/hku-mars/Point-LIO.git`
- Current checked-out commit in `localization/lio/Point-LIO` during this work:
  - `568f60c6179cdb1455ea3739bf7de76147466fbc`
- HKU upstream comparison target used:
  - `upstream/point-lio-with-grid-map`

## What Was Read / Analyzed

- Top-level project architecture and docs were read.
- Entire `localization/lio/Point-LIO` tree was read, including:
  - `src/*`
  - `config/*`
  - `launch/*`
  - `include/*`
  - bundled third-party headers (`IKFoM`, `ivox`, `matplotlibcpp`)
- The actual user test launch was identified as:
  - `~/venom_ws/src/venom_vnv/venom_bringup/launch/examples/mid360_point_lio.launch.py`
- That launch loads this YAML, not the package-internal default:
  - `~/venom_ws/src/venom_vnv/venom_bringup/config/examples/point_lio_mapping.yaml`

## Important Technical Findings

### 1. Fixed time offset was not actually wired through

The bringup YAML already had:

- `~/venom_ws/src/venom_vnv/venom_bringup/config/examples/point_lio_mapping.yaml`
  - `common.time_diff_lidar_to_imu: 0.0`

The package also read this parameter in:

- `~/venom_ws/src/venom_vnv/localization/lio/Point-LIO/src/parameters.cpp`

But before this session it was not effectively connected into the IMU timestamp correction path for the current branch.

HKU upstream does not contain a robust automatic millisecond-grade LiDAR-IMU time offset estimator for this use case. Instead, upstream supports a fixed configured offset and applies it in the IMU callback.

### 2. Mid360 synchronization conclusion from user testing

The user tested fixed time offset tuning and concluded:

- `time_diff_lidar_to_imu = 0.0` works best
- Mid360 appears to already provide good internal synchronization in this setup

Therefore:

- Do not prioritize adding an automatic LiDAR-IMU time offset estimator next
- Keep fixed offset support working, but leave the effective value at `0.0`

### 3. Real high-priority bug found in current branch

In `laserMapping.cpp`, vectors were using `reserve()` and then being written with `operator[]`, which is unsafe and can cause out-of-bounds writes:

- `crossmat_list`
- `pbody_list`

This is especially suspicious under high dynamic motion because it can manifest as unstable behavior or unexplained drift.

## Code Changes Already Made

### A. Fixed vector sizing bug

File:
- `~/venom_ws/src/venom_vnv/localization/lio/Point-LIO/src/laserMapping.cpp`

Change:
- Replaced:
  - `crossmat_list.reserve(feats_down_size);`
  - `pbody_list.reserve(feats_down_size);`
- With:
  - `crossmat_list.resize(feats_down_size);`
  - `pbody_list.resize(feats_down_size);`

### B. Wired fixed LiDAR->IMU time offset into IMU callback

File:
- `~/venom_ws/src/venom_vnv/localization/lio/Point-LIO/src/li_initialization.cpp`

Change:
- IMU timestamp correction now subtracts `time_diff_lidar_to_imu` in `imu_cbk()`

Current relevant line area:
- `~/venom_ws/src/venom_vnv/localization/lio/Point-LIO/src/li_initialization.cpp:160`

### C. Added startup log for configured fixed time offset

File:
- `~/venom_ws/src/venom_vnv/localization/lio/Point-LIO/src/parameters.cpp`

Change:
- Added startup log showing the active fixed LiDAR->IMU offset

Current relevant line area:
- `~/venom_ws/src/venom_vnv/localization/lio/Point-LIO/src/parameters.cpp:303`

## Bringup / Recording Changes Already Made

### Added raw Mid360 recording launch

File:
- `~/venom_ws/src/venom_vnv/venom_bringup/launch/examples/mid360_record_raw.launch.py`

Purpose:
- Start `livox_ros_driver2`
- Record only raw sensor + TF topics
- Save bags in a persistent user directory

Default output directory:
- `~/venom_bags/mid360_raw/`

Recorded topics:
- `/livox/lidar`
- `/livox/imu`
- `/tf`
- `/tf_static`

### Deleted unneeded launch

Deleted file:
- `~/venom_ws/src/venom_vnv/venom_bringup/launch/examples/mid360_point_lio_record.launch.py`

This was removed because the user explicitly said it was not needed.

## Commands Given To User

### Record raw Mid360 bag

```bash
source ~/venom_ws/src/venom_vnv/install/setup.bash
ros2 launch venom_bringup mid360_record_raw.launch.py
```

### Record raw Mid360 bag to a named directory

```bash
source ~/venom_ws/src/venom_vnv/install/setup.bash
ros2 launch venom_bringup mid360_record_raw.launch.py bag_dir:=/Users/liyh/venom_bags/mid360_raw/high_speed_turn_01
```

### Replay a raw bag

```bash
source ~/venom_ws/src/venom_vnv/install/setup.bash
ros2 bag play /Users/liyh/venom_bags/mid360_raw/high_speed_turn_01 --clock
```

### Start current Point-LIO bringup for testing

```bash
source ~/venom_ws/src/venom_vnv/install/setup.bash
ros2 launch venom_bringup mid360_point_lio.launch.py
```

## User's Current Testing Strategy

The user agreed that the right next step is to record several raw bags covering motion intensity levels, then replay the same raw bags repeatedly while changing Point-LIO parameters.

Suggested bag set:

1. `low_speed_01`
2. `mid_speed_01`
3. `high_speed_turn_01`
4. `high_speed_translate_turn_01`

Recording guidance already discussed:

- Each bag should be separate
- Include a few seconds of stillness at start and end
- Prefer 20 to 60 seconds each
- Goal is fair A/B comparison from the same raw input

## Key Performance / Drift Hypotheses To Investigate Next

These were the most relevant likely causes after time offset was ruled out as the main issue:

1. Real-time load under aggressive settings
   - User's active bringup YAML is more aggressive than package default
   - Especially:
     - `~/venom_ws/src/venom_vnv/venom_bringup/config/examples/point_lio_mapping.yaml:9`
       - `filter_size_surf: 0.05`
   - This may improve geometry but can hurt real-time behavior at high speed

2. High-dynamic IMU / propagation quality
   - Current `IMU_Processing.cpp` is relatively light and mostly initialization + passthrough
   - More explicit or refined high-dynamic handling may be needed later

3. Parameter set mismatch for high dynamic motion
   - Need proper replay-based A/B testing, not live tuning

4. Extrinsic sensitivity under vibration / high angular motion
   - `extrinsic_est_en` is currently `False`, which is consistent with upstream recommendations for aggressive motion if extrinsics are known

## Recommended Next Steps For The Next Agent

1. Do not spend more time on automatic LiDAR-IMU fixed time offset estimation unless new evidence appears.
2. Use the new raw-record launch to build a reproducible bag suite.
3. Create a structured replay-based test plan using the user's actual bringup:
   - `~/venom_ws/src/venom_vnv/venom_bringup/launch/examples/mid360_point_lio.launch.py`
4. Compare parameter sets on the same raw bags.
5. Prioritize profiling / timing visibility next.

Recommended immediate work items:

1. Add lightweight profiling output for:
   - preprocess time
   - propagation time
   - update time
   - map incremental time
   - total frame time
2. Create a dedicated high-dynamic YAML variant alongside:
   - `~/venom_ws/src/venom_vnv/venom_bringup/config/examples/point_lio_mapping.yaml`
3. Evaluate whether `filter_size_surf: 0.05` is too aggressive for stable real-time performance during high-speed rotation.

## Files Most Relevant For Follow-Up

- `~/venom_ws/src/venom_vnv/venom_bringup/launch/examples/mid360_point_lio.launch.py`
- `~/venom_ws/src/venom_vnv/venom_bringup/launch/examples/mid360_record_raw.launch.py`
- `~/venom_ws/src/venom_vnv/venom_bringup/config/examples/point_lio_mapping.yaml`
- `~/venom_ws/src/venom_vnv/localization/lio/Point-LIO/src/laserMapping.cpp`
- `~/venom_ws/src/venom_vnv/localization/lio/Point-LIO/src/li_initialization.cpp`
- `~/venom_ws/src/venom_vnv/localization/lio/Point-LIO/src/parameters.cpp`
- `~/venom_ws/src/venom_vnv/localization/lio/Point-LIO/src/IMU_Processing.cpp`
