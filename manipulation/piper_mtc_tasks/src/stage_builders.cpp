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

moveit_msgs::msg::CollisionObject make_collision_cylinder(const SceneCylinder & cylinder)
{
  moveit_msgs::msg::CollisionObject collision;
  collision.id = cylinder.id;
  collision.header.frame_id = cylinder.frame_id;
  collision.operation = moveit_msgs::msg::CollisionObject::ADD;

  shape_msgs::msg::SolidPrimitive primitive;
  primitive.type = shape_msgs::msg::SolidPrimitive::CYLINDER;
  primitive.dimensions = {cylinder.height, cylinder.radius};
  collision.primitives.push_back(primitive);

  geometry_msgs::msg::Pose pose;
  pose.position.x = cylinder.center.x;
  pose.position.y = cylinder.center.y;
  pose.position.z = cylinder.center.z;
  pose.orientation.w = 1.0;
  collision.primitive_poses.push_back(pose);

  return collision;
}

std::vector<moveit_msgs::msg::CollisionObject> make_open_top_bin_collision_boxes(
  const SceneOpenTopBin & bin)
{
  std::vector<moveit_msgs::msg::CollisionObject> collisions;
  collisions.reserve(5);

  const double half_x = 0.5 * bin.size.x;
  const double half_y = 0.5 * bin.size.y;
  const double half_z = 0.5 * bin.size.z;
  const double wall = bin.wall_thickness;

  SceneBox bottom;
  bottom.id = bin.id + "_bottom";
  bottom.frame_id = bin.frame_id;
  bottom.center = {bin.center.x, bin.center.y, bin.center.z - half_z + 0.5 * wall};
  bottom.size = {bin.size.x, bin.size.y, wall};
  collisions.push_back(make_collision_box(bottom));

  SceneBox left_wall;
  left_wall.id = bin.id + "_left_wall";
  left_wall.frame_id = bin.frame_id;
  left_wall.center = {bin.center.x, bin.center.y + half_y - 0.5 * wall, bin.center.z};
  left_wall.size = {bin.size.x, wall, bin.size.z};
  collisions.push_back(make_collision_box(left_wall));

  SceneBox right_wall;
  right_wall.id = bin.id + "_right_wall";
  right_wall.frame_id = bin.frame_id;
  right_wall.center = {bin.center.x, bin.center.y - half_y + 0.5 * wall, bin.center.z};
  right_wall.size = {bin.size.x, wall, bin.size.z};
  collisions.push_back(make_collision_box(right_wall));

  SceneBox front_wall;
  front_wall.id = bin.id + "_front_wall";
  front_wall.frame_id = bin.frame_id;
  front_wall.center = {bin.center.x + half_x - 0.5 * wall, bin.center.y, bin.center.z};
  front_wall.size = {wall, std::max(0.0, bin.size.y - 2.0 * wall), bin.size.z};
  collisions.push_back(make_collision_box(front_wall));

  SceneBox rear_wall;
  rear_wall.id = bin.id + "_rear_wall";
  rear_wall.frame_id = bin.frame_id;
  rear_wall.center = {bin.center.x - half_x + 0.5 * wall, bin.center.y, bin.center.z};
  rear_wall.size = {wall, std::max(0.0, bin.size.y - 2.0 * wall), bin.size.z};
  collisions.push_back(make_collision_box(rear_wall));

  return collisions;
}

std::unique_ptr<stages::ModifyPlanningScene> make_add_scene_stage(
  const TaskParameters & parameters)
{
  auto stage = std::make_unique<stages::ModifyPlanningScene>("add scene objects");
  stage->addObject(make_collision_box(parameters.pickup_table));
  for (const auto & collision : make_open_top_bin_collision_boxes(parameters.place_bin)) {
    stage->addObject(collision);
  }
  stage->addObject(make_collision_cylinder(parameters.pickup_object));
  return stage;
}

std::unique_ptr<stages::ModifyPlanningScene> make_add_pick_object_stage(
  const TaskParameters & parameters)
{
  auto stage = std::make_unique<stages::ModifyPlanningScene>("add pick object");
  stage->addObject(make_collision_cylinder(parameters.pickup_object));
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
  transform.translation().z() =
    parameters.grasp_target_offset.z - parameters.tcp_offset.z;
  return transform;
}

}  // namespace piper_mtc_tasks
