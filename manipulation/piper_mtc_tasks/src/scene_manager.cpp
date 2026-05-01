#include "piper_mtc_tasks/scene_manager.hpp"

#include <array>
#include <string>
#include <vector>

#include "piper_mtc_tasks/stage_builders.hpp"

namespace piper_mtc_tasks
{

namespace
{

std::vector<SceneBox> make_stand_collision_boxes(const SceneBox & tabletop)
{
  const double model_origin_z = tabletop.center.z - 0.423;
  const std::string base_id = tabletop.id.empty() ? "stand" : tabletop.id;

  SceneBox tabletop_box = tabletop;
  tabletop_box.id = base_id + "_tabletop";

  SceneBox pedestal;
  pedestal.id = base_id + "_pedestal";
  pedestal.frame_id = tabletop.frame_id;
  pedestal.center = {tabletop.center.x, tabletop.center.y, model_origin_z + 0.2015};
  pedestal.size = {0.06, 0.06, 0.403};

  SceneBox base;
  base.id = base_id + "_base";
  base.frame_id = tabletop.frame_id;
  base.center = {tabletop.center.x, tabletop.center.y, model_origin_z + 0.01};
  base.size = {0.12, 0.12, 0.02};

  return {tabletop_box, pedestal, base};
}

void append_stand_collision_objects(
  std::vector<moveit_msgs::msg::CollisionObject> & collision_objects,
  const SceneBox & stand)
{
  for (const auto & box : make_stand_collision_boxes(stand)) {
    collision_objects.push_back(make_collision_box(box));
  }
}

}  // namespace

SceneManager::SceneManager(const rclcpp::Logger & logger)
: logger_(logger), planning_scene_interface_("", true)
{
}

bool SceneManager::sync_pick_scene(const TaskParameters & parameters)
{
  planning_scene_interface_.removeCollisionObjects({
    parameters.pickup_stand.id,
    parameters.pickup_stand.id + "_tabletop",
    parameters.pickup_stand.id + "_pedestal",
    parameters.pickup_stand.id + "_base",
    parameters.place_stand.id,
    parameters.place_stand.id + "_tabletop",
    parameters.place_stand.id + "_pedestal",
    parameters.place_stand.id + "_base"});

  std::vector<moveit_msgs::msg::CollisionObject> collision_objects;
  collision_objects.reserve(9);
  append_stand_collision_objects(collision_objects, parameters.pickup_stand);
  append_stand_collision_objects(collision_objects, parameters.place_stand);
  collision_objects.push_back(make_collision_box(parameters.pickup_block));

  const bool applied = planning_scene_interface_.applyCollisionObjects(collision_objects);
  if (!applied) {
    RCLCPP_ERROR(
      logger_,
      "Failed to apply pick scene collision objects to MoveIt's planning scene");
    return false;
  }

  RCLCPP_INFO(
    logger_,
    "Applied pick scene objects: detailed '%s', detailed '%s', '%s'",
    parameters.pickup_stand.id.c_str(),
    parameters.place_stand.id.c_str(),
    parameters.pickup_block.id.c_str());
  return true;
}

}  // namespace piper_mtc_tasks
