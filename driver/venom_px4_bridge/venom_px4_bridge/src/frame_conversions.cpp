#include "venom_px4_bridge/frame_conversions.hpp"

#include <algorithm>
#include <cmath>

#include "tf2/LinearMath/Matrix3x3.h"
#include "tf2/LinearMath/Quaternion.h"
#include "tf2_geometry_msgs/tf2_geometry_msgs.hpp"

namespace venom_px4_bridge
{

namespace
{

bool all_finite(const std::array<float, 4> & values)
{
  return std::all_of(values.begin(), values.end(), [](const float value) {
    return std::isfinite(value);
  });
}

}  // namespace

geometry_msgs::msg::Point ned_to_enu_position(const std::array<float, 3> & ned_position)
{
  geometry_msgs::msg::Point point;
  point.x = ned_position[1];
  point.y = ned_position[0];
  point.z = -ned_position[2];
  return point;
}

geometry_msgs::msg::Vector3 ned_to_enu_vector(const std::array<float, 3> & ned_vector)
{
  geometry_msgs::msg::Vector3 vector;
  vector.x = ned_vector[1];
  vector.y = ned_vector[0];
  vector.z = -ned_vector[2];
  return vector;
}

geometry_msgs::msg::Vector3 frd_to_flu_vector(const std::array<float, 3> & frd_vector)
{
  geometry_msgs::msg::Vector3 vector;
  vector.x = frd_vector[0];
  vector.y = -frd_vector[1];
  vector.z = -frd_vector[2];
  return vector;
}

geometry_msgs::msg::Quaternion px4_to_ros_orientation(const std::array<float, 4> & q_ned_frd)
{
  geometry_msgs::msg::Quaternion orientation;
  orientation.w = 1.0;

  if (!all_finite(q_ned_frd)) {
    return orientation;
  }

  const tf2::Quaternion q_px4(q_ned_frd[1], q_ned_frd[2], q_ned_frd[3], q_ned_frd[0]);
  const tf2::Matrix3x3 r_ned_frd(q_px4);

  const tf2::Matrix3x3 r_enu_ned(
    0.0, 1.0, 0.0,
    1.0, 0.0, 0.0,
    0.0, 0.0, -1.0);

  const tf2::Matrix3x3 r_frd_flu(
    1.0, 0.0, 0.0,
    0.0, -1.0, 0.0,
    0.0, 0.0, -1.0);

  tf2::Matrix3x3 r_enu_flu = r_enu_ned * r_ned_frd * r_frd_flu;
  tf2::Quaternion q_ros;
  r_enu_flu.getRotation(q_ros);
  q_ros.normalize();

  return tf2::toMsg(q_ros);
}

}  // namespace venom_px4_bridge
