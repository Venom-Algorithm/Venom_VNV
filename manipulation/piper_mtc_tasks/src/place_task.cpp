#include "piper_mtc_tasks/place_task.hpp"

#include <algorithm>

#include <geometry_msgs/msg/pose_stamped.hpp>
#include <moveit/task_constructor/container.h>
#include <moveit/task_constructor/stages/compute_ik.h>
#include <moveit/task_constructor/stages/connect.h>
#include <moveit/task_constructor/stages/current_state.h>
#include <moveit/task_constructor/stages/generate_place_pose.h>
#include <moveit/task_constructor/stages/modify_planning_scene.h>

#include "piper_mtc_tasks/gripper_stage_builder.hpp"
#include "piper_mtc_tasks/stage_builders.hpp"

namespace piper_mtc_tasks
{

namespace
{

geometry_msgs::msg::PoseStamped make_place_pose(const TaskParameters & parameters)
{
  const double place_surface_z =
    parameters.place_stand.center.z +
    0.5 * parameters.place_stand.size.z +
    0.5 * parameters.pickup_block.size.z;
  const double pre_place_height = std::max(
    0.14,
    std::max(parameters.lift_min_distance, parameters.lift_max_distance) + 0.08);

  geometry_msgs::msg::PoseStamped pose;
  pose.header.frame_id = parameters.planning_frame;
  pose.pose.orientation.w = 1.0;
  pose.pose.position.x = parameters.place_stand.center.x;
  pose.pose.position.y = parameters.place_stand.center.y;
  pose.pose.position.z = place_surface_z + pre_place_height;
  return pose;
}

std::vector<std::string> place_stand_collision_ids(const TaskParameters & parameters)
{
  return {
    parameters.place_stand.id + "_tabletop",
    parameters.place_stand.id + "_pedestal",
    parameters.place_stand.id + "_base"};
}

}  // namespace

void build_place_task(
  mtc::Task & task,
  const TaskParameters & parameters,
  const PlannerBundle & planners)
{
  task.stages()->setName("piper place task");

  auto current_state = std::make_unique<stages::CurrentState>("current state");
  auto * current_state_ptr = current_state.get();
  task.add(std::move(current_state));

  auto connect = std::make_unique<stages::Connect>(
    "connect to place",
    stages::Connect::GroupPlannerVector{{parameters.arm_group_name, planners.pipeline}});
  connect->setTimeout(parameters.connect_timeout_sec);
  task.add(std::move(connect));

  auto place = std::make_unique<mtc::SerialContainer>("place object");
  task.properties().exposeTo(
    place->properties(), {"group", "eef", "ik_frame"});
  place->properties().configureInitFrom(
    mtc::Stage::PARENT, {"group", "eef", "ik_frame"});

  auto generate_place_pose =
    std::make_unique<stages::GeneratePlacePose>("generate place pose");
  generate_place_pose->properties().configureInitFrom(mtc::Stage::PARENT);
  generate_place_pose->setObject(parameters.pickup_block.id);
  generate_place_pose->setPose(make_place_pose(parameters));
  generate_place_pose->setMonitoredStage(current_state_ptr);

  auto compute_place_ik =
    std::make_unique<stages::ComputeIK>("compute place IK", std::move(generate_place_pose));
  compute_place_ik->setMaxIKSolutions(static_cast<uint32_t>(parameters.max_ik_solutions));
  compute_place_ik->setIgnoreCollisions(false);
  compute_place_ik->setMinSolutionDistance(parameters.min_solution_distance);
  compute_place_ik->setIKFrame(
    make_grasp_frame_transform(parameters),
    parameters.hand_frame);
  compute_place_ik->properties().configureInitFrom(
    mtc::Stage::PARENT, {"group", "eef", "ik_frame"});
  compute_place_ik->properties().configureInitFrom(
    mtc::Stage::INTERFACE, {"target_pose"});
  place->insert(std::move(compute_place_ik));

  auto allow_place_contact =
    std::make_unique<stages::ModifyPlanningScene>("allow place surface contact");
  allow_place_contact->allowCollisions(
    parameters.pickup_block.id,
    place_stand_collision_ids(parameters),
    true);
  place->insert(std::move(allow_place_contact));

  GripperStageBuilder gripper_stages(parameters, planners.interpolation);
  place->insert(gripper_stages.open("open gripper"));

  auto detach_object =
    std::make_unique<stages::ModifyPlanningScene>("detach object");
  detach_object->allowCollisions(parameters.pickup_block.id, parameters.touch_links, true);
  detach_object->detachObject(parameters.pickup_block.id, parameters.hand_frame);
  place->insert(std::move(detach_object));

  task.add(std::move(place));

  task.add(make_cartesian_stage(
    "retreat from place",
    parameters.arm_group_name,
    parameters.hand_frame,
    parameters.retreat_direction_frame,
    parameters.retreat_direction,
    parameters.retreat_min_distance,
    parameters.retreat_max_distance,
    planners.cartesian));

  auto forbid_hand_object_contact =
    std::make_unique<stages::ModifyPlanningScene>("forbid hand-object contact");
  forbid_hand_object_contact->allowCollisions(
    parameters.pickup_block.id,
    parameters.touch_links,
    false);
  task.add(std::move(forbid_hand_object_contact));
}

}  // namespace piper_mtc_tasks
