#include "piper_mtc_tasks/pick_task.hpp"

#include <cmath>
#include <map>
#include <stdexcept>
#include <sstream>

#include <geometry_msgs/msg/pose_stamped.hpp>
#include <geometry_msgs/msg/twist_stamped.hpp>
#include <moveit/task_constructor/container.h>
#include <moveit/task_constructor/stages/connect.h>
#include <moveit/task_constructor/stages/current_state.h>
#include <moveit/task_constructor/stages/modify_planning_scene.h>
#include <moveit/task_constructor/stages/move_to.h>

#include "piper_mtc_tasks/gripper_stage_builder.hpp"
#include "piper_mtc_tasks/stage_builders.hpp"

namespace piper_mtc_tasks
{

namespace
{

bool has_cartesian_distance(double min_distance, double max_distance)
{
  constexpr double kDistanceEpsilon = 1e-6;
  return std::abs(min_distance) > kDistanceEpsilon || std::abs(max_distance) > kDistanceEpsilon;
}

std::unique_ptr<stages::ModifyPlanningScene> make_allow_object_contact_stage(
  const TaskParameters & parameters)
{
  auto stage =
    std::make_unique<stages::ModifyPlanningScene>("allow object contact");
  stage->allowCollisions(
    parameters.pickup_object.id,
    parameters.touch_links,
    true);
  return stage;
}

std::vector<double> non_empty_candidates(
  const std::vector<double> & configured,
  double fallback)
{
  if (!configured.empty()) {
    return configured;
  }
  return std::vector<double>{fallback};
}

std::string make_candidate_name(
  const XYZ & grasp_target_offset,
  double x,
  double y,
  double z,
  const XYZ & approach_direction,
  double roll,
  double pitch,
  double yaw)
{
  std::ostringstream name;
  name << "pick target=(" << grasp_target_offset.x << ","
       << grasp_target_offset.y << "," << grasp_target_offset.z << ")"
       << " pregrasp=(" << x << "," << y << "," << z << ")"
       << " approach=(" << approach_direction.x << ","
       << approach_direction.y << "," << approach_direction.z << ")"
       << " rpy=(" << roll << "," << pitch << "," << yaw << ")";
  return name.str();
}

std::vector<XYZ> direction_candidates(
  const std::vector<double> & configured,
  const XYZ & fallback)
{
  if (configured.empty()) {
    return std::vector<XYZ>{fallback};
  }
  if (configured.size() % 3 != 0) {
    throw std::runtime_error(
            "Parameter 'top_down_approach_direction_candidates' must contain "
            "a multiple of 3 values.");
  }

  std::vector<XYZ> candidates;
  candidates.reserve(configured.size() / 3);
  for (size_t i = 0; i < configured.size(); i += 3) {
    candidates.push_back(XYZ{configured[i], configured[i + 1], configured[i + 2]});
  }
  return candidates;
}

template<typename Builder>
void add_top_down_candidates(
  mtc::Task & task,
  const TaskParameters & parameters,
  Builder && builder)
{
  const auto grasp_target_x_candidates = non_empty_candidates(
    parameters.top_down_grasp_target_x_candidates,
    parameters.grasp_target_offset.x);
  const auto grasp_target_y_candidates = non_empty_candidates(
    parameters.top_down_grasp_target_y_candidates,
    parameters.grasp_target_offset.y);
  const auto grasp_target_z_candidates = non_empty_candidates(
    parameters.top_down_grasp_target_z_candidates,
    parameters.grasp_target_offset.z);
  const auto x_candidates = non_empty_candidates(
    parameters.top_down_pregrasp_x_candidates,
    parameters.pregrasp_offset.x);
  const auto y_candidates = non_empty_candidates(
    parameters.top_down_pregrasp_y_candidates,
    parameters.pregrasp_offset.y);
  const auto z_candidates = non_empty_candidates(
    parameters.top_down_pregrasp_z_candidates,
    parameters.pregrasp_offset.z);
  const auto approach_direction_candidates = direction_candidates(
    parameters.top_down_approach_direction_candidates,
    parameters.approach_direction);
  const auto roll_candidates = non_empty_candidates(
    parameters.top_down_roll_candidates,
    parameters.grasp_orientation.roll);
  const auto pitch_candidates = non_empty_candidates(
    parameters.top_down_pitch_candidates,
    parameters.grasp_orientation.pitch);
  const auto yaw_candidates = non_empty_candidates(
    parameters.top_down_yaw_candidates,
    parameters.grasp_orientation.yaw);

  auto alternatives = std::make_unique<mtc::Fallbacks>("top-down grasp candidates");
  task.properties().exposeTo(
    alternatives->properties(), {"group", "eef", "ik_frame"});
  alternatives->properties().configureInitFrom(
    mtc::Stage::PARENT, {"group", "eef", "ik_frame"});
  for (const double grasp_x : grasp_target_x_candidates) {
    for (const double grasp_y : grasp_target_y_candidates) {
      for (const double grasp_z : grasp_target_z_candidates) {
        for (const double pregrasp_x : x_candidates) {
          for (const double pregrasp_y : y_candidates) {
            for (const double pregrasp_z : z_candidates) {
              for (const auto & approach_direction : approach_direction_candidates) {
                for (const double roll : roll_candidates) {
                  for (const double pitch : pitch_candidates) {
                    for (const double yaw : yaw_candidates) {
                      TaskParameters selected = parameters;
                      selected.grasp_target_offset.x = grasp_x;
                      selected.grasp_target_offset.y = grasp_y;
                      selected.grasp_target_offset.z = grasp_z;
                      selected.pregrasp_offset.x = pregrasp_x;
                      selected.pregrasp_offset.y = pregrasp_y;
                      selected.pregrasp_offset.z = pregrasp_z;
                      selected.approach_direction = approach_direction;
                      selected.grasp_orientation.roll = roll;
                      selected.grasp_orientation.pitch = pitch;
                      selected.grasp_orientation.yaw = yaw;

                      alternatives->insert(builder(selected));
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
  task.add(std::move(alternatives));
}

geometry_msgs::msg::PoseStamped make_pick_object_pose(
  const TaskParameters & parameters)
{
  geometry_msgs::msg::PoseStamped pose;
  pose.header.frame_id = parameters.pickup_object.frame_id;
  pose.pose.position.x = parameters.pickup_object.center.x;
  pose.pose.position.y = parameters.pickup_object.center.y;
  pose.pose.position.z = parameters.pickup_object.center.z;
  pose.pose.orientation.w = 1.0;
  return pose;
}

std::unique_ptr<stages::MoveTo> make_pose_goal_stage(
  const std::string & stage_name,
  const TaskParameters & parameters,
  const mtc::solvers::PlannerInterfacePtr & planner,
  const XYZ & target_offset)
{
  auto stage = std::make_unique<stages::MoveTo>(stage_name, planner);
  stage->setGroup(parameters.arm_group_name);
  TaskParameters target_parameters = parameters;
  target_parameters.grasp_target_offset = target_offset;
  stage->setIKFrame(
    make_grasp_frame_transform(target_parameters),
    parameters.hand_frame);
  stage->setGoal(make_pick_object_pose(parameters));
  return stage;
}

std::unique_ptr<mtc::SerialContainer> make_grasp_ik_probe_sequence(
  const std::string & name,
  const TaskParameters & parameters,
  const PlannerBundle & planners)
{
  auto probe = std::make_unique<mtc::SerialContainer>(name);
  probe->properties().configureInitFrom(
    mtc::Stage::PARENT, {"group", "eef", "ik_frame"});
  probe->insert(make_pose_goal_stage(
    "move to grasp pose",
    parameters,
    planners.pipeline,
    parameters.grasp_target_offset));
  return probe;
}

std::unique_ptr<mtc::SerialContainer> make_grasp_motion_sequence(
  const std::string & name,
  const TaskParameters & parameters,
  const PlannerBundle & planners,
  bool include_pregrasp)
{
  auto sequence = std::make_unique<mtc::SerialContainer>(name);
  sequence->properties().configureInitFrom(
    mtc::Stage::PARENT, {"group", "eef", "ik_frame"});

  if (include_pregrasp) {
    sequence->insert(make_pose_goal_stage(
      "move to pregrasp pose",
      parameters,
      planners.pipeline,
      parameters.pregrasp_offset));
  }

  sequence->insert(make_pose_goal_stage(
    "move to grasp pose",
    parameters,
    planners.pipeline,
    parameters.grasp_target_offset));
  return sequence;
}

void append_pick_tail(
  mtc::SerialContainer & sequence,
  const TaskParameters & parameters,
  const PlannerBundle & planners,
  GripperStageBuilder & gripper_stages,
  bool include_lift)
{
  auto allow_object_collision =
    std::make_unique<stages::ModifyPlanningScene>("allow object collision");
  allow_object_collision->allowCollisions(
    parameters.pickup_object.id,
    parameters.touch_links,
    true);
  sequence.insert(std::move(allow_object_collision));

  sequence.insert(gripper_stages.close("close gripper"));

  auto attach_object =
    std::make_unique<stages::ModifyPlanningScene>("attach object");
  attach_object->allowCollisions(
    parameters.pickup_object.id,
    parameters.touch_links,
    true);
  attach_object->attachObject(parameters.pickup_object.id, parameters.hand_frame);
  sequence.insert(std::move(attach_object));

  if (include_lift && has_cartesian_distance(parameters.lift_min_distance, parameters.lift_max_distance)) {
    sequence.insert(make_cartesian_stage(
      "lift object",
      parameters.arm_group_name,
      parameters.hand_frame,
      parameters.lift_direction_frame,
      parameters.lift_direction,
      parameters.lift_min_distance,
      parameters.lift_max_distance,
      planners.cartesian));
  }
}

std::unique_ptr<mtc::SerialContainer> make_pick_sequence(
  const std::string & name,
  const TaskParameters & parameters,
  const PlannerBundle & planners,
  GripperStageBuilder & gripper_stages,
  bool include_pregrasp,
  bool include_lift)
{
  auto sequence = make_grasp_motion_sequence(
    name,
    parameters,
    planners,
    include_pregrasp);
  if (parameters.arm_only_reach_test) {
    return sequence;
  }
  append_pick_tail(*sequence, parameters, planners, gripper_stages, include_lift);
  return sequence;
}

}  // namespace

void build_pick_task(
  mtc::Task & task,
  const TaskParameters & parameters,
  const PlannerBundle & planners)
{
  task.stages()->setName("piper pick task");

  auto current_state = std::make_unique<stages::CurrentState>("current state");
  task.add(std::move(current_state));
  if (!parameters.disable_scene_objects) {
    task.add(make_add_scene_stage(parameters));
  } else {
    task.add(make_add_pick_object_stage(parameters));
  }

  GripperStageBuilder gripper_stages(parameters, planners.interpolation);
  if (!parameters.skip_open_gripper_stage) {
    task.add(gripper_stages.open("open gripper"));
  }
  auto allow_object_contact = make_allow_object_contact_stage(parameters);
  task.add(std::move(allow_object_contact));

  if (!parameters.skip_connect_stage) {
    auto connect = std::make_unique<stages::Connect>(
      "connect to pick",
      stages::Connect::GroupPlannerVector{{parameters.arm_group_name, planners.pipeline}});
    connect->setTimeout(parameters.connect_timeout_sec);
    task.add(std::move(connect));
  }

  if (parameters.top_down_strategy_enabled) {
    add_top_down_candidates(
      task,
      parameters,
      [&](const TaskParameters & selected) {
        auto pick = make_pick_sequence(
          make_candidate_name(
            selected.grasp_target_offset,
            selected.pregrasp_offset.x,
            selected.pregrasp_offset.y,
            selected.pregrasp_offset.z,
            selected.approach_direction,
            selected.grasp_orientation.roll,
            selected.grasp_orientation.pitch,
            selected.grasp_orientation.yaw),
          selected,
          planners,
          gripper_stages,
          true,
          true);
        task.properties().exposeTo(
          pick->properties(), {"group", "eef", "ik_frame"});
        return pick;
      });
  } else {
    const bool include_pregrasp =
      has_cartesian_distance(parameters.approach_min_distance, parameters.approach_max_distance) ||
      std::abs(parameters.pregrasp_offset.x - parameters.grasp_target_offset.x) > 1e-6 ||
      std::abs(parameters.pregrasp_offset.y - parameters.grasp_target_offset.y) > 1e-6 ||
      std::abs(parameters.pregrasp_offset.z - parameters.grasp_target_offset.z) > 1e-6;
    auto pick = make_pick_sequence(
      "pick sequence",
      parameters,
      planners,
      gripper_stages,
      include_pregrasp,
      true);
    task.properties().exposeTo(
      pick->properties(), {"group", "eef", "ik_frame"});
    task.add(std::move(pick));
  }

  if (!parameters.top_down_strategy_enabled &&
    has_cartesian_distance(parameters.retreat_min_distance, parameters.retreat_max_distance))
  {
    task.add(make_cartesian_stage(
      "retreat",
      parameters.arm_group_name,
      parameters.hand_frame,
      parameters.retreat_direction_frame,
      parameters.retreat_direction,
      parameters.retreat_min_distance,
      parameters.retreat_max_distance,
      planners.cartesian));
  }
}

void build_grasp_ik_probe_task(
  mtc::Task & task,
  const TaskParameters & parameters,
  const PlannerBundle & planners)
{
  task.stages()->setName("piper grasp IK probe");

  auto current_state = std::make_unique<stages::CurrentState>("current state");
  task.add(std::move(current_state));
  if (!parameters.disable_scene_objects) {
    task.add(make_add_scene_stage(parameters));
  } else {
    task.add(make_add_pick_object_stage(parameters));
  }

  // Diagnostic IK probing should answer "is this grasp geometry solvable?"
  // even when the real gripper is not perfectly parked in an open start state.
  // Skipping the explicit open-gripper stage avoids false negatives caused by
  // start-state collisions or gripper controller timeouts before IK is tested.
  auto allow_object_contact = make_allow_object_contact_stage(parameters);
  task.add(std::move(allow_object_contact));

  if (!parameters.skip_connect_stage) {
    auto connect = std::make_unique<stages::Connect>(
      "connect to grasp IK probe",
      stages::Connect::GroupPlannerVector{{parameters.arm_group_name, planners.pipeline}});
    connect->setTimeout(parameters.connect_timeout_sec);
    task.add(std::move(connect));
  }

  if (parameters.top_down_strategy_enabled) {
    add_top_down_candidates(
      task,
      parameters,
      [&](const TaskParameters & selected) {
        auto probe = make_grasp_ik_probe_sequence(
          make_candidate_name(
            selected.grasp_target_offset,
            selected.pregrasp_offset.x,
            selected.pregrasp_offset.y,
            selected.pregrasp_offset.z,
            selected.approach_direction,
            selected.grasp_orientation.roll,
            selected.grasp_orientation.pitch,
          selected.grasp_orientation.yaw),
          selected,
          planners);
        task.properties().exposeTo(
          probe->properties(), {"group", "eef", "ik_frame"});
        return probe;
      });
  } else {
    auto probe = make_grasp_ik_probe_sequence(
      "grasp IK probe",
      parameters,
      planners);
    task.properties().exposeTo(
      probe->properties(), {"group", "eef", "ik_frame"});
    task.add(std::move(probe));
  }
}

}  // namespace piper_mtc_tasks
