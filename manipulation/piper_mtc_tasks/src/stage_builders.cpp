#include "piper_mtc_tasks/stage_builders.hpp"

#include <cmath>

#include <tf2/LinearMath/Quaternion.h>
#include <tf2_geometry_msgs/tf2_geometry_msgs.hpp>

#include <shape_msgs/msg/solid_primitive.hpp>

namespace piper_mtc_tasks
{

moveit_msgs::msg::CollisionObject make_collision_box(const SceneBox & box)
{
  moveit_msgs::msg::CollisionObject collision;
  collision.id = box.id;
  collision.header.frame_id = box.frame_id;
  collision.operation = moveit_msgs::msg::CollisionObject::ADD;

  shape_msgs::msg::SolidPrimitive primitive;
  primitive.type = shape_msgs::msg::SolidPrimitive::BOX;
  primitive.dimensions = {box.size.x, box.size.y, box.size.z};
  collision.primitives.push_back(primitive);

  geometry_msgs::msg::Pose pose;
  pose.position.x = box.center.x;
  pose.position.y = box.center.y;
  pose.position.z = box.center.z;
  pose.orientation.w = 1.0;
  collision.primitive_poses.push_back(pose);

  return collision;
}

std::unique_ptr<stages::ModifyPlanningScene> make_add_scene_stage(
  const TaskParameters & parameters)
{
  auto stage = std::make_unique<stages::ModifyPlanningScene>("add scene objects");
  stage->addObject(make_collision_box(parameters.pickup_stand));
  stage->addObject(make_collision_box(parameters.place_stand));
  stage->addObject(make_collision_box(parameters.pickup_block));
  return stage;
}

std::unique_ptr<stages::MoveTo> make_named_gripper_stage(
  const std::string & stage_name,
  const std::string & group_name,
  const std::string & named_target,
  const std::shared_ptr<mtc::solvers::JointInterpolationPlanner> & planner)
{
  auto stage = std::make_unique<stages::MoveTo>(stage_name, planner);
  stage->setGroup(group_name);
  stage->setGoal(named_target);
  return stage;
}

std::unique_ptr<stages::MoveRelative> make_cartesian_stage(
  const std::string & stage_name,
  const std::string & group_name,
  const std::string & link_name,
  const std::string & direction_frame,
  const XYZ & direction,
  double min_distance,
  double max_distance,
  const mtc::solvers::PlannerInterfacePtr & planner)
{
  auto stage = std::make_unique<stages::MoveRelative>(stage_name, planner);
  stage->properties().set("marker_ns", stage_name);
  stage->setGroup(group_name);
  stage->setIKFrame(link_name);
  stage->setMinMaxDistance(min_distance, max_distance);

  geometry_msgs::msg::Vector3Stamped vector;
  vector.header.frame_id = direction_frame;
  const double direction_norm = std::sqrt(
    direction.x * direction.x + direction.y * direction.y + direction.z * direction.z);
  if (direction_norm > 1e-9) {
    vector.vector.x = direction.x / direction_norm;
    vector.vector.y = direction.y / direction_norm;
    vector.vector.z = direction.z / direction_norm;
  }
  stage->setDirection(vector);
  return stage;
}

Eigen::Isometry3d make_grasp_frame_transform(const TaskParameters & parameters)
{
  tf2::Quaternion quaternion;
  quaternion.setRPY(
    parameters.grasp_orientation.roll,
    parameters.grasp_orientation.pitch,
    parameters.grasp_orientation.yaw);

  Eigen::Quaterniond eigen_quaternion(
    quaternion.w(),
    quaternion.x(),
    quaternion.y(),
    quaternion.z());

  Eigen::Isometry3d transform = Eigen::Isometry3d::Identity();
  transform.linear() = eigen_quaternion.normalized().toRotationMatrix();
  transform.translation().x() =
    parameters.grasp_target_offset.x - parameters.tcp_offset.x;
  transform.translation().y() =
    parameters.grasp_target_offset.y - parameters.tcp_offset.y;
  const double top_down_height_bias =
    parameters.top_down_strategy_enabled ? (parameters.pickup_block.size.z * 0.5) : 0.0;
  transform.translation().z() =
    top_down_height_bias +
    parameters.grasp_target_offset.z -
    parameters.tcp_offset.z;
  return transform;
}

}  // namespace piper_mtc_tasks
