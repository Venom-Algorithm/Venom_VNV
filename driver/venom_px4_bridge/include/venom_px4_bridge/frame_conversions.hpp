#pragma once

#include <array>

#include "geometry_msgs/msg/point.hpp"
#include "geometry_msgs/msg/quaternion.hpp"
#include "geometry_msgs/msg/vector3.hpp"

namespace venom_px4_bridge
{

geometry_msgs::msg::Point ned_to_enu_position(const std::array<float, 3> & ned_position);

geometry_msgs::msg::Vector3 ned_to_enu_vector(const std::array<float, 3> & ned_vector);

geometry_msgs::msg::Vector3 frd_to_flu_vector(const std::array<float, 3> & frd_vector);

geometry_msgs::msg::Quaternion px4_to_ros_orientation(
  const std::array<float, 4> & q_ned_frd);

}  // namespace venom_px4_bridge
