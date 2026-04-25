#!/usr/bin/env bash
set -euo pipefail

SRC=/ros_ws/src/venom_vnv

# ── 1. COLCON_IGNORE：排除 hardware-only 包 ───────────────────
IGNORE_PKGS=(
    "driver/livox_ros_driver2"
    "driver/ros2_hik_camera"
    "driver/ugv_sdk"
    "driver/scout_ros2"
    "driver/hunter_ros2"
    "driver/piper_ros"
    "driver/venom_serial_driver"
    "driver/venom_px4_bridge"
    "localization/lio/Point-LIO"
    "localization/lio/Fast-LIO"
    "localization/lio/rf2o_laser_odometry"
    "localization/relocalization/small_gicp_relocalization"
    # Gazebo Classic 包，arm64 上不可用；x86 CI 上同样跳过（只验证非仿真包）
    "simulation/venom_nav_simulation/src/rm_simulation/venom_mid360_simulation"
    "simulation/venom_nav_simulation/src/rm_simulation/livox_laser_simulation_RO2"
)

for pkg in "${IGNORE_PKGS[@]}"; do
    [ -d "${SRC}/${pkg}" ] && touch "${SRC}/${pkg}/COLCON_IGNORE"
done

# ── 2. source ROS ─────────────────────────────────────────────
set +u  # ROS setup scripts reference unbound variables
source /opt/ros/humble/setup.bash
set -u

# ── 3. rosdep install ─────────────────────────────────────────
cd /ros_ws
rosdep install \
    -r \
    --from-paths src \
    --ignore-src \
    --rosdistro humble \
    -y \
    || true   # 非致命 key 警告不中断 CI

# ── 4. colcon build ───────────────────────────────────────────
MAKEFLAGS="-j${MAKE_JOBS:-2}" colcon build \
    --cmake-args \
        -DCMAKE_BUILD_TYPE=Release \
        -DROS_EDITION=ROS2 \
        -DHUMBLE_ROS=humble \
        -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
    --parallel-workers "${COLCON_WORKERS:-2}" \
    --event-handlers console_cohesion+

echo "BUILD COMPLETE"
