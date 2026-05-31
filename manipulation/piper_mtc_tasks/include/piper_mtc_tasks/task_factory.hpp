#pragma once

#include <memory>

#include <moveit/task_constructor/task.h>
#include <rclcpp/rclcpp.hpp>

#include "piper_mtc_tasks/pick_task.hpp"
#include "piper_mtc_tasks/task_parameters.hpp"

namespace piper_mtc_tasks
{

namespace mtc = moveit::task_constructor;

class TaskFactory
{
public:
  TaskFactory(
    const rclcpp::Node::SharedPtr & node,
    const TaskParameters & parameters);

  mtc::Task create_pick_task() const;
  mtc::Task create_place_task() const;
  mtc::Task create_grasp_ik_probe_task() const;
  mtc::Task create_move_home_task() const;

private:
  PlannerBundle create_planners() const;
  void configure_task_properties(mtc::Task & task) const;

  rclcpp::Node::SharedPtr node_;
  TaskParameters parameters_;
};

}  // namespace piper_mtc_tasks
