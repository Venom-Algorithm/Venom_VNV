#pragma once

#include <memory>
#include <string>
#include <vector>

#include <Eigen/Geometry>

#include <geometry_msgs/msg/vector3_stamped.hpp>
#include <moveit_msgs/msg/collision_object.hpp>
#include <moveit/task_constructor/solvers/planner_interface.h>
#include <moveit/task_constructor/solvers/cartesian_path.h>
#include <moveit/task_constructor/solvers/joint_interpolation.h>
#include <moveit/task_constructor/stages/modify_planning_scene.h>
#include <moveit/task_constructor/stages/move_relative.h>
#include <moveit/task_constructor/stages/move_to.h>

#include "piper_mtc_tasks/task_parameters.hpp"

namespace piper_mtc_tasks
{

namespace mtc = moveit::task_constructor;
namespace stages = moveit::task_constructor::stages;

moveit_msgs::msg::CollisionObject make_collision_box(const SceneBox & box);
moveit_msgs::msg::CollisionObject make_collision_cylinder(const SceneCylinder & cylinder);
std::vector<moveit_msgs::msg::CollisionObject> make_open_top_bin_collision_boxes(
  const SceneOpenTopBin & bin);

std::unique_ptr<stages::ModifyPlanningScene> make_add_scene_stage(
  const TaskParameters & parameters);
std::unique_ptr<stages::ModifyPlanningScene> make_add_pick_object_stage(
  const TaskParameters & parameters);

std::unique_ptr<stages::MoveTo> make_named_gripper_stage(
  const std::string & stage_name,
  const std::string & group_name,
  const std::string & named_target,
  const std::shared_ptr<mtc::solvers::JointInterpolationPlanner> & planner);

std::unique_ptr<stages::MoveRelative> make_cartesian_stage(
  const std::string & stage_name,
  const std::string & group_name,
  const std::string & link_name,
  const std::string & direction_frame,
  const XYZ & direction,
  double min_distance,
  double max_distance,
  const mtc::solvers::PlannerInterfacePtr & planner);

Eigen::Isometry3d make_grasp_frame_transform(const TaskParameters & parameters);

}  // namespace piper_mtc_tasks
