#pragma once

#include <memory>
#include <string>

#include <moveit/task_constructor/solvers/joint_interpolation.h>
#include <moveit/task_constructor/stages/move_to.h>

#include "piper_mtc_tasks/task_parameters.hpp"

namespace piper_mtc_tasks
{

namespace mtc = moveit::task_constructor;
namespace stages = moveit::task_constructor::stages;

class GripperStageBuilder
{
public:
  GripperStageBuilder(
    const TaskParameters & parameters,
    const std::shared_ptr<mtc::solvers::JointInterpolationPlanner> & planner);

  std::unique_ptr<stages::MoveTo> open(const std::string & stage_name) const;
  std::unique_ptr<stages::MoveTo> close(const std::string & stage_name) const;

private:
  std::unique_ptr<stages::MoveTo> named_posture(
    const std::string & stage_name,
    const std::string & named_target) const;

  const TaskParameters & parameters_;
  std::shared_ptr<mtc::solvers::JointInterpolationPlanner> planner_;
};

}  // namespace piper_mtc_tasks
