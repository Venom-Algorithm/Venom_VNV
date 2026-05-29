#pragma once

#include <vector>

#include <moveit/planning_scene_interface/planning_scene_interface.h>
#include <rclcpp/rclcpp.hpp>

#include "piper_mtc_tasks/task_parameters.hpp"

namespace piper_mtc_tasks
{

class SceneManager
{
public:
  explicit SceneManager(const rclcpp::Logger & logger);

  bool sync_pick_scene(const TaskParameters & parameters);

private:
  bool wait_for_collision_objects(
    const std::vector<std::string> & object_ids,
    double timeout_sec);

  rclcpp::Logger logger_;
  moveit::planning_interface::PlanningSceneInterface planning_scene_interface_;
};

}  // namespace piper_mtc_tasks
