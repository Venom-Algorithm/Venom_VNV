#include "piper_mtc_tasks/gripper_stage_builder.hpp"

#include <map>

namespace piper_mtc_tasks
{

GripperStageBuilder::GripperStageBuilder(
  const TaskParameters & parameters,
  const std::shared_ptr<mtc::solvers::JointInterpolationPlanner> & planner)
: parameters_(parameters), planner_(planner)
{
}

std::unique_ptr<stages::MoveTo> GripperStageBuilder::open(
  const std::string & stage_name) const
{
  if (parameters_.gripper_open_joint7 >= 0.0) {
    auto stage = std::make_unique<stages::MoveTo>(stage_name, planner_);
    stage->setGroup(parameters_.gripper_group_name);
    stage->setGoal(std::map<std::string, double>{{"joint7", parameters_.gripper_open_joint7}});
    return stage;
  }
  return named_posture(stage_name, parameters_.gripper_open_named_target);
}

std::unique_ptr<stages::MoveTo> GripperStageBuilder::close(
  const std::string & stage_name) const
{
  if (parameters_.gripper_close_joint7 >= 0.0) {
    auto stage = std::make_unique<stages::MoveTo>(stage_name, planner_);
    stage->setGroup(parameters_.gripper_group_name);
    stage->setGoal(std::map<std::string, double>{{"joint7", parameters_.gripper_close_joint7}});
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
