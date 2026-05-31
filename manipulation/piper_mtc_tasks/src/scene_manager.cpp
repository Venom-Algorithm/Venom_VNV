#include "piper_mtc_tasks/scene_manager.hpp"

#include <chrono>

#include <array>
#include <string>
#include <vector>

#include "piper_mtc_tasks/stage_builders.hpp"

namespace piper_mtc_tasks
{

namespace
{

std::vector<std::string> make_open_top_bin_collision_ids(const SceneOpenTopBin & bin)
{
  return {
    bin.id + "_bottom",
    bin.id + "_left_wall",
    bin.id + "_right_wall",
    bin.id + "_front_wall",
    bin.id + "_rear_wall"};
}

}  // namespace

SceneManager::SceneManager(const rclcpp::Logger & logger)
: logger_(logger), planning_scene_interface_("", true)
{
}

bool SceneManager::sync_pick_scene(const TaskParameters & parameters)
{
  std::vector<std::string> ids_to_remove = {
    parameters.pickup_table.id,
    parameters.pickup_object.id};
  const auto bin_ids = make_open_top_bin_collision_ids(parameters.place_bin);
  ids_to_remove.insert(ids_to_remove.end(), bin_ids.begin(), bin_ids.end());
  planning_scene_interface_.removeCollisionObjects(ids_to_remove);

  std::vector<moveit_msgs::msg::CollisionObject> collision_objects;
  collision_objects.reserve(7);
  collision_objects.push_back(make_collision_box(parameters.pickup_table));
  const auto bin_collisions = make_open_top_bin_collision_boxes(parameters.place_bin);
  collision_objects.insert(collision_objects.end(), bin_collisions.begin(), bin_collisions.end());
  collision_objects.push_back(make_collision_cylinder(parameters.pickup_object));

  const bool applied = planning_scene_interface_.applyCollisionObjects(collision_objects);
  if (!applied) {
    RCLCPP_ERROR(
      logger_,
      "Failed to apply pick scene collision objects to MoveIt's planning scene");
    return false;
  }

  if (!wait_for_collision_objects(ids_to_remove, 2.0)) {
    RCLCPP_WARN(
      logger_,
      "Pick scene objects were not immediately observable after apply; continuing because the task also injects scene objects.");
  }

  RCLCPP_INFO(
    logger_,
    "Applied pick scene objects: table '%s', bin '%s', object '%s'",
    parameters.pickup_table.id.c_str(),
    parameters.place_bin.id.c_str(),
    parameters.pickup_object.id.c_str());
  return true;
}

bool SceneManager::wait_for_collision_objects(
  const std::vector<std::string> & object_ids,
  double timeout_sec)
{
  const auto deadline =
    std::chrono::steady_clock::now() + std::chrono::duration<double>(timeout_sec);

  while (std::chrono::steady_clock::now() < deadline) {
    const auto objects = planning_scene_interface_.getObjects(object_ids);
    bool all_present = true;
    for (const auto & object_id : object_ids) {
      if (objects.find(object_id) == objects.end()) {
        all_present = false;
        break;
      }
    }

    if (all_present) {
      return true;
    }

    rclcpp::sleep_for(std::chrono::milliseconds(100));
  }

  const auto objects = planning_scene_interface_.getObjects(object_ids);
  std::vector<std::string> missing_ids;
  for (const auto & object_id : object_ids) {
    if (objects.find(object_id) == objects.end()) {
      missing_ids.push_back(object_id);
    }
  }

  if (!missing_ids.empty()) {
    std::ostringstream missing_stream;
    for (std::size_t index = 0; index < missing_ids.size(); ++index) {
      if (index > 0) {
        missing_stream << ", ";
      }
      missing_stream << missing_ids[index];
    }
    RCLCPP_WARN(
      logger_,
      "Timed out waiting for planning scene objects: %s",
      missing_stream.str().c_str());
  }

  return missing_ids.empty();
}

}  // namespace piper_mtc_tasks
