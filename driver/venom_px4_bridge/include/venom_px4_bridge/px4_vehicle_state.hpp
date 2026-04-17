#pragma once

#include <cstdint>

namespace venom_px4_bridge
{

struct Px4VehicleState
{
  bool has_status{false};
  bool has_odometry{false};
  bool has_battery{false};
  bool has_control_mode{false};
  bool has_failsafe_flags{false};
  bool has_timesync{false};

  bool armed{false};
  bool failsafe{false};
  bool offboard_enabled{false};
  bool preflight_checks_pass{false};

  std::uint8_t nav_state{0};
  float battery_remaining{-1.0F};
  std::int64_t estimated_time_offset_us{0};
};

}  // namespace venom_px4_bridge
