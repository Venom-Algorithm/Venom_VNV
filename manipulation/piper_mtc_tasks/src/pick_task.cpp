#include "piper_mtc_tasks/pick_task.hpp"

#include <cmath>
#include <stdexcept>
#include <sstream>

#include <moveit/task_constructor/container.h>
#include <moveit/task_constructor/stages/compute_ik.h>
#include <moveit/task_constructor/stages/connect.h>
#include <moveit/task_constructor/stages/current_state.h>
#include <moveit/task_constructor/stages/generate_grasp_pose.h>
#include <moveit/task_constructor/stages/modify_planning_scene.h>

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
    parameters.pickup_block.id,
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

std::unique_ptr<stages::ComputeIK> make_grasp_ik_stage(
  const TaskParameters & parameters,
  mtc::Stage * allow_object_contact_ptr)
{
  auto generate_grasp_pose =
    std::make_unique<stages::GenerateGraspPose>("generate grasp pose");
  generate_grasp_pose->properties().configureInitFrom(mtc::Stage::PARENT);
  generate_grasp_pose->setObject(parameters.pickup_block.id);
  generate_grasp_pose->setPreGraspPose(parameters.gripper_open_named_target);
  generate_grasp_pose->setAngleDelta(parameters.grasp_angle_delta);
  generate_grasp_pose->setMonitoredStage(allow_object_contact_ptr);

  auto compute_ik =
    std::make_unique<stages::ComputeIK>("compute grasp IK", std::move(generate_grasp_pose));
  compute_ik->setMaxIKSolutions(static_cast<uint32_t>(parameters.max_ik_solutions));
  compute_ik->setIgnoreCollisions(false);
  compute_ik->setMinSolutionDistance(parameters.min_solution_distance);
  compute_ik->setIKFrame(
    make_grasp_frame_transform(parameters),
    parameters.hand_frame);
  compute_ik->properties().configureInitFrom(
    mtc::Stage::PARENT, {"group", "eef", "ik_frame"});
  compute_ik->properties().configureInitFrom(
    mtc::Stage::INTERFACE, {"target_pose"});
  return compute_ik;
}

std::unique_ptr<mtc::SerialContainer> make_grasp_ik_probe_sequence(
  const std::string & name,
  const TaskParameters & parameters,
  const PlannerBundle & planners,
  mtc::Stage * allow_object_contact_ptr)
{
  auto probe = std::make_unique<mtc::SerialContainer>(name);
  probe->properties().configureInitFrom(
    mtc::Stage::PARENT, {"group", "eef", "ik_frame"});
  if (has_cartesian_distance(parameters.approach_min_distance, parameters.approach_max_distance)) {
    probe->insert(make_cartesian_stage(
      "approach object",
      parameters.arm_group_name,
      parameters.hand_frame,
      parameters.approach_direction_frame,
      parameters.approach_direction,
      parameters.approach_min_distance,
      parameters.approach_max_distance,
      planners.cartesian));
  }
  probe->insert(make_grasp_ik_stage(parameters, allow_object_contact_ptr));
  return probe;
}

std::unique_ptr<mtc::SerialContainer> make_pick_sequence(
  const std::string & name,
  const TaskParameters & parameters,
  const PlannerBundle & planners,
  GripperStageBuilder & gripper_stages,
  mtc::Stage * allow_object_contact_ptr)
{
  auto pick = std::make_unique<mtc::SerialContainer>(name);
  pick->properties().configureInitFrom(
    mtc::Stage::PARENT, {"group", "eef", "ik_frame"});

  if (has_cartesian_distance(parameters.approach_min_distance, parameters.approach_max_distance)) {
    pick->insert(make_cartesian_stage(
      "approach object",
      parameters.arm_group_name,
      parameters.hand_frame,
      parameters.approach_direction_frame,
      parameters.approach_direction,
      parameters.approach_min_distance,
      parameters.approach_max_distance,
      planners.cartesian));
  }

  pick->insert(make_grasp_ik_stage(parameters, allow_object_contact_ptr));

  pick->insert(gripper_stages.close("close gripper"));

  auto attach_object =
    std::make_unique<stages::ModifyPlanningScene>("attach object");
  attach_object->allowCollisions(
    parameters.pickup_block.id,
    parameters.touch_links,
    true);
  attach_object->attachObject(parameters.pickup_block.id, parameters.hand_frame);
  pick->insert(std::move(attach_object));

  pick->insert(make_cartesian_stage(
    "lift object",
    parameters.arm_group_name,
    parameters.hand_frame,
    parameters.lift_direction_frame,
    parameters.lift_direction,
    parameters.lift_min_distance,
    parameters.lift_max_distance,
    planners.pipeline));

  return pick;
}

}  // namespace

void build_pick_task(
  mtc::Task & task,
  const TaskParameters & parameters,
  const PlannerBundle & planners)
{
  task.stages()->setName("piper pick task");

  task.add(std::make_unique<stages::CurrentState>("current state"));

  GripperStageBuilder gripper_stages(parameters, planners.interpolation);
  task.add(gripper_stages.open("open gripper"));
  auto allow_object_contact = make_allow_object_contact_stage(parameters);
  auto * allow_object_contact_ptr = allow_object_contact.get();
  task.add(std::move(allow_object_contact));

  auto connect = std::make_unique<stages::Connect>(
    "connect to pick",
    stages::Connect::GroupPlannerVector{{parameters.arm_group_name, planners.pipeline}});
  connect->setTimeout(parameters.connect_timeout_sec);
  task.add(std::move(connect));

  if (parameters.top_down_strategy_enabled) {
    auto alternatives = std::make_unique<mtc::Fallbacks>("top-down grasp strategy");
    task.properties().exposeTo(
      alternatives->properties(), {"group", "eef", "ik_frame"});
    alternatives->properties().configureInitFrom(
      mtc::Stage::PARENT, {"group", "eef", "ik_frame"});

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

    for (const double grasp_x : grasp_target_x_candidates) {
      for (const double grasp_y : grasp_target_y_candidates) {
        for (const double grasp_z : grasp_target_z_candidates) {
          for (const double x : x_candidates) {
            for (const double y : y_candidates) {
              for (const double z : z_candidates) {
                for (const auto & approach_direction : approach_direction_candidates) {
                  for (const double roll : roll_candidates) {
                    for (const double pitch : pitch_candidates) {
                      for (const double yaw : yaw_candidates) {
                        TaskParameters candidate = parameters;
                        candidate.grasp_target_offset.x = grasp_x;
                        candidate.grasp_target_offset.y = grasp_y;
                        candidate.grasp_target_offset.z = grasp_z;
                        candidate.pregrasp_offset.x = x;
                        candidate.pregrasp_offset.y = y;
                        candidate.pregrasp_offset.z = z;
                        candidate.approach_direction = approach_direction;
                        candidate.grasp_orientation.roll = roll;
                        candidate.grasp_orientation.pitch = pitch;
                        candidate.grasp_orientation.yaw = yaw;
                        auto pick = make_pick_sequence(
                          make_candidate_name(
                            candidate.grasp_target_offset,
                            x,
                            y,
                            z,
                            approach_direction,
                            roll,
                            pitch,
                            yaw),
                          candidate,
                          planners,
                          gripper_stages,
                          allow_object_contact_ptr);
                        alternatives->properties().exposeTo(
                          pick->properties(), {"group", "eef", "ik_frame"});
                        alternatives->insert(std::move(pick));
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
  } else {
    auto pick = make_pick_sequence(
      "pick object",
      parameters,
      planners,
      gripper_stages,
      allow_object_contact_ptr);
    task.properties().exposeTo(
      pick->properties(), {"group", "eef", "ik_frame"});
    task.add(std::move(pick));
  }

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

void build_grasp_ik_probe_task(
  mtc::Task & task,
  const TaskParameters & parameters,
  const PlannerBundle & planners)
{
  task.stages()->setName("piper grasp IK probe");

  task.add(std::make_unique<stages::CurrentState>("current state"));

  GripperStageBuilder gripper_stages(parameters, planners.interpolation);
  task.add(gripper_stages.open("open gripper"));
  auto allow_object_contact = make_allow_object_contact_stage(parameters);
  auto * allow_object_contact_ptr = allow_object_contact.get();
  task.add(std::move(allow_object_contact));

  auto connect = std::make_unique<stages::Connect>(
    "connect to grasp IK probe",
    stages::Connect::GroupPlannerVector{{parameters.arm_group_name, planners.pipeline}});
  connect->setTimeout(parameters.connect_timeout_sec);
  task.add(std::move(connect));

  if (parameters.top_down_strategy_enabled) {
    auto alternatives = std::make_unique<mtc::Fallbacks>("top-down grasp IK strategy probe");
    task.properties().exposeTo(
      alternatives->properties(), {"group", "eef", "ik_frame"});
    alternatives->properties().configureInitFrom(
      mtc::Stage::PARENT, {"group", "eef", "ik_frame"});

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

    for (const double grasp_x : grasp_target_x_candidates) {
      for (const double grasp_y : grasp_target_y_candidates) {
        for (const double grasp_z : grasp_target_z_candidates) {
          for (const double x : x_candidates) {
            for (const double y : y_candidates) {
              for (const double z : z_candidates) {
                for (const auto & approach_direction : approach_direction_candidates) {
                  for (const double roll : roll_candidates) {
                    for (const double pitch : pitch_candidates) {
                      for (const double yaw : yaw_candidates) {
                        TaskParameters candidate = parameters;
                        candidate.grasp_target_offset.x = grasp_x;
                        candidate.grasp_target_offset.y = grasp_y;
                        candidate.grasp_target_offset.z = grasp_z;
                        candidate.pregrasp_offset.x = x;
                        candidate.pregrasp_offset.y = y;
                        candidate.pregrasp_offset.z = z;
                        candidate.approach_direction = approach_direction;
                        candidate.grasp_orientation.roll = roll;
                        candidate.grasp_orientation.pitch = pitch;
                        candidate.grasp_orientation.yaw = yaw;
                        auto probe = make_grasp_ik_probe_sequence(
                          make_candidate_name(
                            candidate.grasp_target_offset,
                            x,
                            y,
                            z,
                            approach_direction,
                            roll,
                            pitch,
                            yaw),
                          candidate,
                          planners,
                          allow_object_contact_ptr);
                        alternatives->properties().exposeTo(
                          probe->properties(), {"group", "eef", "ik_frame"});
                        alternatives->insert(std::move(probe));
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
  } else {
    auto probe = make_grasp_ik_probe_sequence(
      "grasp IK probe",
      parameters,
      planners,
      allow_object_contact_ptr);
    task.properties().exposeTo(
      probe->properties(), {"group", "eef", "ik_frame"});
    task.add(std::move(probe));
  }
}

}  // namespace piper_mtc_tasks
