#pragma once

#include <memory>

#include <moveit/task_constructor/solvers/cartesian_path.h>
#include <moveit/task_constructor/solvers/joint_interpolation.h>
#include <moveit/task_constructor/solvers/pipeline_planner.h>
#include <moveit/task_constructor/task.h>

#include "piper_mtc_tasks/task_parameters.hpp"

namespace piper_mtc_tasks
{

namespace mtc = moveit::task_constructor;

struct PlannerBundle
{
  std::shared_ptr<mtc::solvers::PipelinePlanner> pipeline;
  std::shared_ptr<mtc::solvers::CartesianPath> cartesian;
  std::shared_ptr<mtc::solvers::JointInterpolationPlanner> interpolation;
};

void build_pick_task(
  mtc::Task & task,
  const TaskParameters & parameters,
  const PlannerBundle & planners);

void build_grasp_ik_probe_task(
  mtc::Task & task,
  const TaskParameters & parameters,
  const PlannerBundle & planners);

}  // namespace piper_mtc_tasks
