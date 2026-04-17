#pragma once

#include <cstdint>
#include <string>

namespace venom_px4_bridge
{

inline std::string nav_state_to_string(const std::uint8_t nav_state)
{
  switch (nav_state) {
    case 0:
      return "MANUAL";
    case 1:
      return "ALTCTL";
    case 2:
      return "POSCTL";
    case 3:
      return "AUTO_MISSION";
    case 4:
      return "AUTO_LOITER";
    case 5:
      return "AUTO_RTL";
    case 10:
      return "ACRO";
    case 12:
      return "DESCEND";
    case 13:
      return "TERMINATION";
    case 14:
      return "OFFBOARD";
    case 15:
      return "STAB";
    case 17:
      return "AUTO_TAKEOFF";
    case 18:
      return "AUTO_LAND";
    case 21:
      return "ORBIT";
    default:
      return "UNKNOWN(" + std::to_string(nav_state) + ")";
  }
}

}  // namespace venom_px4_bridge
