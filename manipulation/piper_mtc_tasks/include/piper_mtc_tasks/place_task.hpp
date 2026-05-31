#pragma once

#include <moveit/task_constructor/task.h>

#include "piper_mtc_tasks/pick_task.hpp"

namespace piper_mtc_tasks
{

namespace mtc = moveit::task_constructor;

void build_place_task(
  mtc::Task & task,
  const TaskParameters & parameters,
  const PlannerBundle & planners);

}  // namespace piper_mtc_tasks
