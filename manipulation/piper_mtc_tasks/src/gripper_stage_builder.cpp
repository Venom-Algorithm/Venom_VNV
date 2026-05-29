#include "piper_mtc_tasks/gripper_stage_builder.hpp"

#include <algorithm>
#include <map>

namespace piper_mtc_tasks
{

namespace
{

bool use_direct_gripper_target(double joint7_target)
{
  return joint7_target >= -0.5;
}

double normalize_gripper_joint7_target(double joint7_target)
{
  if (joint7_target > 0.0) {
    return -std::clamp(joint7_target, 0.0, 0.035);
  }
  return std::clamp(joint7_target, -0.040, 0.0);
}

}  // namespace

GripperStageBuilder::GripperStageBuilder(
  const TaskParameters & parameters,
  const std::shared_ptr<mtc::solvers::JointInterpolationPlanner> & planner)
: parameters_(parameters), planner_(planner)
{
}

std::unique_ptr<stages::MoveTo> GripperStageBuilder::open(
  const std::string & stage_name) const
{
  if (use_direct_gripper_target(parameters_.gripper_open_joint7)) {
    auto stage = std::make_unique<stages::MoveTo>(stage_name, planner_);
    stage->setGroup(parameters_.gripper_group_name);
    stage->setGoal(
      std::map<std::string, double>{
        {"joint7", normalize_gripper_joint7_target(parameters_.gripper_open_joint7)}});
    return stage;
  }
  return named_posture(stage_name, parameters_.gripper_open_named_target);
}

std::unique_ptr<stages::MoveTo> GripperStageBuilder::close(
  const std::string & stage_name) const
{
  if (use_direct_gripper_target(parameters_.gripper_close_joint7)) {
    auto stage = std::make_unique<stages::MoveTo>(stage_name, planner_);
    stage->setGroup(parameters_.gripper_group_name);
    stage->setGoal(
      std::map<std::string, double>{
        {"joint7", normalize_gripper_joint7_target(parameters_.gripper_close_joint7)}});
    return stage;
  }
  return named_posture(stage_name, parameters_.gripper_close_named_target);
}

std::unique_ptr<stages::MoveTo> GripperStageBuilder::named_posture(
  const std::string & stage_name,
  const std::string & named_target) const
{
  auto stage = std::make_unique<stages::MoveTo>(stage_name, planner_);
  stage->setGroup(parameters_.gripper_group_name);
  stage->setGoal(named_target);
  return stage;
}

}  // namespace piper_mtc_tasks
