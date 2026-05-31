#include "piper_mtc_tasks/task_factory.hpp"

#include <moveit/task_constructor/solvers/cartesian_path.h>
#include <moveit/task_constructor/solvers/joint_interpolation.h>
#include <moveit/task_constructor/solvers/pipeline_planner.h>
#include <moveit/task_constructor/stages/current_state.h>
#include <moveit/task_constructor/stages/move_to.h>
#include <moveit/trajectory_processing/iterative_time_parameterization.h>

#include "piper_mtc_tasks/gripper_stage_builder.hpp"
#include "piper_mtc_tasks/pick_task.hpp"
#include "piper_mtc_tasks/place_task.hpp"
#include "piper_mtc_tasks/stage_builders.hpp"

namespace piper_mtc_tasks
{

namespace
{

XYZ read_xyz_parameter(rclcpp::Node & node, const std::string & name)
{
  const auto values = node.get_parameter(name).as_double_array();
  if (values.size() != 3) {
    throw std::runtime_error(
            "Parameter '" + name + "' must contain exactly 3 elements.");
  }
  return XYZ{values[0], values[1], values[2]};
}

RPY read_rpy_parameter(rclcpp::Node & node, const std::string & name)
{
  const auto values = node.get_parameter(name).as_double_array();
  if (values.size() != 3) {
    throw std::runtime_error(
            "Parameter '" + name + "' must contain exactly 3 elements.");
  }
  return RPY{values[0], values[1], values[2]};
}

std::vector<XYZ> read_xyz_triples_parameter(rclcpp::Node & node, const std::string & name)
{
  const auto values = node.get_parameter(name).as_double_array();
  if (values.empty()) {
    return {};
  }
  if (values.size() % 3 != 0) {
    throw std::runtime_error(
            "Parameter '" + name + "' must contain xyz triples.");
  }

  std::vector<XYZ> triples;
  triples.reserve(values.size() / 3);
  for (std::size_t index = 0; index < values.size(); index += 3) {
    triples.push_back(XYZ{values[index], values[index + 1], values[index + 2]});
  }
  return triples;
}

SceneBox read_scene_box(
  rclcpp::Node & node,
  const std::string & prefix,
  const std::string & default_id,
  const std::string & frame_id)
{
  SceneBox box;
  box.id = node.get_parameter(prefix + ".id").as_string();
  if (box.id.empty()) {
    box.id = default_id;
  }
  box.frame_id = frame_id;
  box.center.x = node.get_parameter(prefix + ".x").as_double();
  box.center.y = node.get_parameter(prefix + ".y").as_double();
  box.center.z = node.get_parameter(prefix + ".z").as_double();
  box.size.x = node.get_parameter(prefix + ".size_x").as_double();
  box.size.y = node.get_parameter(prefix + ".size_y").as_double();
  box.size.z = node.get_parameter(prefix + ".size_z").as_double();
  return box;
}

SceneCylinder read_scene_cylinder(
  rclcpp::Node & node,
  const std::string & prefix,
  const std::string & default_id,
  const std::string & frame_id)
{
  SceneCylinder cylinder;
  cylinder.id = node.get_parameter(prefix + ".id").as_string();
  if (cylinder.id.empty()) {
    cylinder.id = default_id;
  }
  cylinder.frame_id = frame_id;
  cylinder.center.x = node.get_parameter(prefix + ".x").as_double();
  cylinder.center.y = node.get_parameter(prefix + ".y").as_double();
  cylinder.center.z = node.get_parameter(prefix + ".z").as_double();
  cylinder.radius = node.get_parameter(prefix + ".radius").as_double();
  cylinder.height = node.get_parameter(prefix + ".height").as_double();
  return cylinder;
}

SceneOpenTopBin read_scene_open_top_bin(
  rclcpp::Node & node,
  const std::string & prefix,
  const std::string & default_id,
  const std::string & frame_id)
{
  SceneOpenTopBin bin;
  bin.id = node.get_parameter(prefix + ".id").as_string();
  if (bin.id.empty()) {
    bin.id = default_id;
  }
  bin.frame_id = frame_id;
  bin.center.x = node.get_parameter(prefix + ".x").as_double();
  bin.center.y = node.get_parameter(prefix + ".y").as_double();
  bin.center.z = node.get_parameter(prefix + ".z").as_double();
  bin.size.x = node.get_parameter(prefix + ".size_x").as_double();
  bin.size.y = node.get_parameter(prefix + ".size_y").as_double();
  bin.size.z = node.get_parameter(prefix + ".size_z").as_double();
  bin.wall_thickness = node.get_parameter(prefix + ".wall_thickness").as_double();
  return bin;
}

}  // namespace

void declare_task_parameters(rclcpp::Node & node)
{
  node.declare_parameter<std::string>("action_name", "/manipulation/execute_task");
  node.declare_parameter<std::string>("planning_frame", "base_link");
  node.declare_parameter<std::string>("arm_group_name", "arm");
  node.declare_parameter<std::string>("gripper_group_name", "gripper");
  node.declare_parameter<std::string>("hand_frame", "gripper_grasp_center");
  node.declare_parameter<std::string>("arm_home_named_target", "zero");
  node.declare_parameter<std::string>("gripper_open_named_target", "open");
  node.declare_parameter<std::string>("gripper_close_named_target", "close");
  node.declare_parameter<bool>("move_home_open_gripper", true);
  node.declare_parameter<std::string>("approach_direction_frame", "");
  node.declare_parameter<std::string>("lift_direction_frame", "");
  node.declare_parameter<std::string>("retreat_direction_frame", "");
  node.declare_parameter<double>("gripper_open_joint7", -1.0);
  node.declare_parameter<double>("gripper_close_joint7", -1.0);
  node.declare_parameter<std::string>("pipeline_planner_id", "ompl");
  node.declare_parameter<int64_t>("max_solutions", 3);
  node.declare_parameter<int64_t>("max_ik_solutions", 16);
  node.declare_parameter<double>("min_solution_distance", 1.0);
  node.declare_parameter<double>("connect_timeout_sec", 20.0);
  node.declare_parameter<double>("plan_timeout_sec", 30.0);
  node.declare_parameter<double>("approach_min_distance", 0.035);
  node.declare_parameter<double>("approach_max_distance", 0.055);
  node.declare_parameter<double>("lift_min_distance", 0.10);
  node.declare_parameter<double>("lift_max_distance", 0.18);
  node.declare_parameter<double>("retreat_min_distance", 0.02);
  node.declare_parameter<double>("retreat_max_distance", 0.06);
  node.declare_parameter<double>("cartesian_step_size", 0.005);
  node.declare_parameter<double>("cartesian_jump_threshold", 0.0);
  node.declare_parameter<double>("cartesian_velocity_scaling", 0.15);
  node.declare_parameter<double>("cartesian_acceleration_scaling", 0.10);
  node.declare_parameter<double>("grasp_angle_delta", 0.261799387799);
  node.declare_parameter<bool>("execute_on_plan", true);
  node.declare_parameter<bool>("diagnostic_ik_only", false);
  node.declare_parameter<bool>("pick_only", false);
  node.declare_parameter<bool>("use_direct_visual_pick_fallback", false);
  node.declare_parameter<bool>("top_down_strategy_enabled", false);
  node.declare_parameter<bool>("disable_scene_objects", false);
  node.declare_parameter<bool>("arm_only_reach_test", false);
  node.declare_parameter<bool>("skip_connect_stage", false);
  node.declare_parameter<bool>("skip_open_gripper_stage", false);
  node.declare_parameter<bool>("move_home_before_pick", false);
  node.declare_parameter<bool>("use_contact_aware_gripper_close", true);
  node.declare_parameter<bool>("enable_gazebo_attachment", false);
  node.declare_parameter<bool>("gazebo_attach_require_gripper_closed", true);
  node.declare_parameter<int64_t>("autostart_task_type", 0);
  node.declare_parameter<double>("gazebo_attach_update_hz", 30.0);
  node.declare_parameter<double>("gazebo_attach_min_delay_sec", 8.0);
  node.declare_parameter<double>("gazebo_attach_max_distance", 0.18);
  node.declare_parameter<double>("gazebo_attach_max_horizontal_distance", 0.08);
  node.declare_parameter<double>("gazebo_attach_gripper_joint7_threshold", 0.005);
  node.declare_parameter<std::string>("gazebo_attachment_frame", "gripper_grasp_center");
  node.declare_parameter<std::string>("gazebo_attach_robot_model", "piper");
  node.declare_parameter<std::string>("gazebo_attach_robot_link", "link6");
  node.declare_parameter<std::string>("gazebo_attach_object_model", "pick_target_block");
  node.declare_parameter<std::string>("gazebo_attach_object_link", "block_link");
  node.declare_parameter<std::vector<double>>("tcp_offset_xyz", {0.0, 0.0, 0.0});
  node.declare_parameter<std::vector<double>>("grasp_target_offset_xyz", {0.0, 0.0, 0.0});
  node.declare_parameter<std::vector<double>>("pregrasp_offset_xyz", {0.0, 0.0, 0.0});
  node.declare_parameter<std::vector<double>>("approach_direction_xyz", {0.0, 0.0, 1.0});
  node.declare_parameter<std::vector<double>>("lift_direction_xyz", {0.0, 0.0, 1.0});
  node.declare_parameter<std::vector<double>>("retreat_direction_xyz", {-1.0, 0.0, 0.0});
  node.declare_parameter<std::vector<double>>(
    "grasp_orientation_rpy", {-3.136, 1.529, -3.131});
  node.declare_parameter<std::vector<double>>("top_down_grasp_target_x_candidates", std::vector<double>{});
  node.declare_parameter<std::vector<double>>("top_down_grasp_target_y_candidates", std::vector<double>{});
  node.declare_parameter<std::vector<double>>("top_down_grasp_target_z_candidates", std::vector<double>{});
  node.declare_parameter<std::vector<double>>("top_down_pregrasp_x_candidates", {0.0});
  node.declare_parameter<std::vector<double>>("top_down_pregrasp_y_candidates", {0.0});
  node.declare_parameter<std::vector<double>>("top_down_pregrasp_z_candidates", {0.07, 0.09, 0.11});
  node.declare_parameter<std::vector<double>>(
    "top_down_approach_direction_candidates",
    std::vector<double>{
      0.0, 0.0, -1.0,
      0.30, 0.0, -1.0,
      -0.30, 0.0, -1.0,
      0.0, 0.30, -1.0,
      0.0, -0.30, -1.0});
  node.declare_parameter<std::vector<double>>("top_down_roll_candidates", {-3.14159265359, 3.14159265359});
  node.declare_parameter<std::vector<double>>("top_down_pitch_candidates", {-0.8, -0.4, 0.0, 0.4});
  node.declare_parameter<std::vector<double>>(
    "top_down_yaw_candidates", {-1.57079632679, 0.0, 1.57079632679, 3.14159265359});
  node.declare_parameter<std::vector<std::string>>(
    "pickup_object.touch_links",
    std::vector<std::string>{"link7", "link8"});
  node.declare_parameter<bool>("vision_target.enabled", false);
  node.declare_parameter<bool>("vision_target.require_single_target", true);
  node.declare_parameter<bool>("vision_target.require_valid_signal", true);
  node.declare_parameter<bool>("vision_target.compute_grasp_offsets", true);
  node.declare_parameter<bool>("vision_target.lock_lateral_offsets_to_zero", false);
  node.declare_parameter<double>("vision_target.target_timeout_sec", 0.5);
  node.declare_parameter<double>("vision_target.wait_after_home_timeout_sec", 2.0);
  node.declare_parameter<double>("vision_target.min_target_confidence", 0.7);
  node.declare_parameter<double>("vision_target.pregrasp_distance", 0.07);
  node.declare_parameter<double>("vision_target.grasp_clearance", 0.01);
  node.declare_parameter<double>("vision_target.grasp_z_offset", 0.0);
  node.declare_parameter<double>("vision_target.collision_scale_xy", 0.85);
  node.declare_parameter<double>("vision_target.collision_scale_z", 0.90);
  node.declare_parameter<std::string>("vision_target.grasp_strategy", "radial_side");
  node.declare_parameter<std::string>("vision_target.object_shape", "cylinder");
  node.declare_parameter<std::vector<double>>(
    "vision_target.target_position_bias_xyz", {0.0, 0.0, 0.0});
  node.declare_parameter<std::vector<double>>(
    "vision_target.default_target_size_xyz", {0.053, 0.053, 0.134});
  node.declare_parameter<std::vector<double>>(
    "vision_target.workspace_min_xyz", {-10.0, -10.0, -10.0});
  node.declare_parameter<std::vector<double>>(
    "vision_target.workspace_max_xyz", {10.0, 10.0, 10.0});
  node.declare_parameter<std::vector<double>>(
    "vision_target.yaw_candidate_offsets",
    std::vector<double>{-0.2617993878, -0.0872664626, 0.0, 0.0872664626, 0.2617993878});
  node.declare_parameter<std::vector<std::string>>(
    "vision_target.allowed_target_classes",
    std::vector<std::string>{"block", "cube"});
  node.declare_parameter<bool>("observe_pose.enabled", false);
  node.declare_parameter<std::vector<double>>(
    "observe_pose.xyz", {0.25, 0.0, 0.35});
  node.declare_parameter<std::vector<double>>(
    "observe_pose.rpy", {3.14159, 0.0, -1.5708});
  node.declare_parameter<bool>("pre_place.enabled", false);
  node.declare_parameter<double>("pre_place.heading_offset", 0.0);
  node.declare_parameter<std::string>("pre_place.base_joint_name", "joint1");
  node.declare_parameter<double>("pre_place.min_delta", 0.02);
  node.declare_parameter<bool>("pre_place.coarse_base_first", true);
  node.declare_parameter<std::string>("pre_place.retract_joint3_name", "joint3");
  node.declare_parameter<std::string>("pre_place.retract_joint4_name", "joint4");
  node.declare_parameter<double>("pre_place.retract_joint3_delta", 0.0);
  node.declare_parameter<double>("pre_place.retract_joint4_delta", 0.0);
  node.declare_parameter<bool>("pre_place.hover_after_base", false);
  node.declare_parameter<double>("pre_place.hover_margin_xy", 0.04);
  node.declare_parameter<double>("pre_place.hover_margin_z", 0.03);
  node.declare_parameter<bool>("classification_place.enabled", false);
  node.declare_parameter<std::vector<double>>(
    "classification_place.platform_slots_xyz",
    std::vector<double>{0.0, 0.20, 0.30, 0.0, 0.28, 0.30});
  node.declare_parameter<std::vector<std::string>>(
    "classification_place.platform_slot_classes",
    std::vector<std::string>{"white_block", "black_block"});
  node.declare_parameter<std::vector<std::string>>(
    "classification_place.box_classes",
    std::vector<std::string>{"white_box", "black_box"});
  node.declare_parameter<std::vector<double>>(
    "classification_place.pregrasp_offset_xyz", {0.0, 0.0, 0.07});
  node.declare_parameter<std::vector<double>>(
    "classification_place.lift_offset_xyz", {0.0, 0.0, 0.07});
  node.declare_parameter<std::vector<double>>(
    "classification_place.release_offset_xyz", {0.0, 0.0, 0.10});
  node.declare_parameter<std::vector<double>>(
    "classification_place.grasp_orientation_rpy", {0.0, 1.57079632679, 1.57079632679});
  node.declare_parameter<double>("classification_place.box_target_timeout_sec", 3.0);
  node.declare_parameter<double>("classification_place.min_box_confidence", 0.5);
  node.declare_parameter<std::string>(
    "classification_place.target_fusion_node_name", "/grasp_target_fusion");
  node.declare_parameter<bool>("classification_place.set_fusion_target_class", true);
  node.declare_parameter<double>("classification_place.target_switch_settle_sec", 0.20);
  node.declare_parameter<std::string>("repeat_visual_pick.target_class", "bottle");
  node.declare_parameter<std::vector<int64_t>>(
    "repeat_visual_pick.place_indices",
    std::vector<int64_t>{0, 1});
  node.declare_parameter<std::string>(
    "repeat_visual_pick.target_fusion_node_name", "/grasp_target_fusion");
  node.declare_parameter<bool>("repeat_visual_pick.set_fusion_target_class", true);
  node.declare_parameter<double>("repeat_visual_pick.target_switch_settle_sec", 0.20);
  node.declare_parameter<double>("repeat_visual_pick.delay_between_picks_sec", 1.0);
  node.declare_parameter<std::string>(
    "flame_tracking.set_enabled_service", "/flame_arm_tracker/set_enabled");
  node.declare_parameter<double>("flame_tracking.service_timeout_sec", 3.0);
  node.declare_parameter<std::vector<double>>(
    "place_target.offset_xyz", {0.0, 0.0, 0.0});
  node.declare_parameter<double>("place_target.release_height", 0.03);
  node.declare_parameter<std::vector<double>>(
    "place_target.orientation_rpy", {0.0, 0.0, 0.0});
  node.declare_parameter<bool>("place_target.release_after_pre_place", false);
  node.declare_parameter<bool>("place_target.allow_direct_release_fallback", false);
  node.declare_parameter<double>("place_target.direct_release_retreat_z", 0.06);
  node.declare_parameter<int64_t>("place_target.fixed_pose_index", 0);
  node.declare_parameter<std::vector<double>>(
    "place_target.fixed_pose_candidates_xyz",
    std::vector<double>{0.0, 0.20, 0.30, 0.0, 0.28, 0.30});

  node.declare_parameter<std::string>("pickup_table.id", "pickup_table");
  node.declare_parameter<double>("pickup_table.x", 0.35);
  node.declare_parameter<double>("pickup_table.y", 0.0);
  node.declare_parameter<double>("pickup_table.z", 0.39);
  node.declare_parameter<double>("pickup_table.size_x", 0.60);
  node.declare_parameter<double>("pickup_table.size_y", 0.40);
  node.declare_parameter<double>("pickup_table.size_z", 0.02);

  node.declare_parameter<std::string>("place_bin.id", "rear_drop_bin");
  node.declare_parameter<double>("place_bin.x", -0.08);
  node.declare_parameter<double>("place_bin.y", 0.10);
  node.declare_parameter<double>("place_bin.z", 0.04);
  node.declare_parameter<double>("place_bin.size_x", 0.15);
  node.declare_parameter<double>("place_bin.size_y", 0.10);
  node.declare_parameter<double>("place_bin.size_z", 0.08);
  node.declare_parameter<double>("place_bin.wall_thickness", 0.01);

  node.declare_parameter<std::string>("pickup_object.id", "redbull_can");
  node.declare_parameter<double>("pickup_object.x", 0.25);
  node.declare_parameter<double>("pickup_object.y", 0.0);
  node.declare_parameter<double>("pickup_object.z", 0.467);
  node.declare_parameter<double>("pickup_object.radius", 0.0265);
  node.declare_parameter<double>("pickup_object.height", 0.134);
}

TaskParameters load_task_parameters(rclcpp::Node & node)
{
  TaskParameters parameters;
  parameters.action_name = node.get_parameter("action_name").as_string();
  parameters.planning_frame = node.get_parameter("planning_frame").as_string();
  parameters.arm_group_name = node.get_parameter("arm_group_name").as_string();
  parameters.gripper_group_name = node.get_parameter("gripper_group_name").as_string();
  parameters.hand_frame = node.get_parameter("hand_frame").as_string();
  parameters.arm_home_named_target = node.get_parameter("arm_home_named_target").as_string();
  parameters.gripper_open_named_target =
    node.get_parameter("gripper_open_named_target").as_string();
  parameters.gripper_close_named_target =
    node.get_parameter("gripper_close_named_target").as_string();
  parameters.move_home_open_gripper = node.get_parameter("move_home_open_gripper").as_bool();
  parameters.approach_direction_frame =
    node.get_parameter("approach_direction_frame").as_string();
  parameters.lift_direction_frame =
    node.get_parameter("lift_direction_frame").as_string();
  parameters.retreat_direction_frame =
    node.get_parameter("retreat_direction_frame").as_string();
  if (parameters.approach_direction_frame.empty()) {
    parameters.approach_direction_frame = parameters.hand_frame;
  }
  if (parameters.lift_direction_frame.empty()) {
    parameters.lift_direction_frame = parameters.planning_frame;
  }
  if (parameters.retreat_direction_frame.empty()) {
    parameters.retreat_direction_frame = parameters.planning_frame;
  }
  parameters.gripper_open_joint7 = node.get_parameter("gripper_open_joint7").as_double();
  parameters.gripper_close_joint7 = node.get_parameter("gripper_close_joint7").as_double();
  parameters.pipeline_planner_id = node.get_parameter("pipeline_planner_id").as_string();
  parameters.max_solutions = node.get_parameter("max_solutions").as_int();
  parameters.max_ik_solutions = node.get_parameter("max_ik_solutions").as_int();
  parameters.min_solution_distance = node.get_parameter("min_solution_distance").as_double();
  parameters.connect_timeout_sec = node.get_parameter("connect_timeout_sec").as_double();
  parameters.plan_timeout_sec = node.get_parameter("plan_timeout_sec").as_double();
  parameters.approach_min_distance =
    node.get_parameter("approach_min_distance").as_double();
  parameters.approach_max_distance =
    node.get_parameter("approach_max_distance").as_double();
  parameters.lift_min_distance = node.get_parameter("lift_min_distance").as_double();
  parameters.lift_max_distance = node.get_parameter("lift_max_distance").as_double();
  parameters.retreat_min_distance =
    node.get_parameter("retreat_min_distance").as_double();
  parameters.retreat_max_distance =
    node.get_parameter("retreat_max_distance").as_double();
  parameters.cartesian_step_size = node.get_parameter("cartesian_step_size").as_double();
  parameters.cartesian_jump_threshold =
    node.get_parameter("cartesian_jump_threshold").as_double();
  parameters.cartesian_velocity_scaling =
    node.get_parameter("cartesian_velocity_scaling").as_double();
  parameters.cartesian_acceleration_scaling =
    node.get_parameter("cartesian_acceleration_scaling").as_double();
  parameters.grasp_angle_delta = node.get_parameter("grasp_angle_delta").as_double();
  parameters.execute_on_plan = node.get_parameter("execute_on_plan").as_bool();
  parameters.diagnostic_ik_only = node.get_parameter("diagnostic_ik_only").as_bool();
  parameters.pick_only = node.get_parameter("pick_only").as_bool();
  parameters.use_direct_visual_pick_fallback =
    node.get_parameter("use_direct_visual_pick_fallback").as_bool();
  parameters.top_down_strategy_enabled =
    node.get_parameter("top_down_strategy_enabled").as_bool();
  parameters.disable_scene_objects = node.get_parameter("disable_scene_objects").as_bool();
  parameters.arm_only_reach_test = node.get_parameter("arm_only_reach_test").as_bool();
  parameters.skip_connect_stage = node.get_parameter("skip_connect_stage").as_bool();
  parameters.skip_open_gripper_stage =
    node.get_parameter("skip_open_gripper_stage").as_bool();
  parameters.move_home_before_pick =
    node.get_parameter("move_home_before_pick").as_bool();
  parameters.use_contact_aware_gripper_close =
    node.get_parameter("use_contact_aware_gripper_close").as_bool();
  parameters.enable_gazebo_attachment =
    node.get_parameter("enable_gazebo_attachment").as_bool();
  parameters.gazebo_attach_require_gripper_closed =
    node.get_parameter("gazebo_attach_require_gripper_closed").as_bool();
  parameters.autostart_task_type = node.get_parameter("autostart_task_type").as_int();
  parameters.gazebo_attach_update_hz =
    node.get_parameter("gazebo_attach_update_hz").as_double();
  parameters.gazebo_attach_min_delay_sec =
    node.get_parameter("gazebo_attach_min_delay_sec").as_double();
  parameters.gazebo_attach_max_distance =
    node.get_parameter("gazebo_attach_max_distance").as_double();
  parameters.gazebo_attach_max_horizontal_distance =
    node.get_parameter("gazebo_attach_max_horizontal_distance").as_double();
  parameters.gazebo_attach_gripper_joint7_threshold =
    node.get_parameter("gazebo_attach_gripper_joint7_threshold").as_double();
  parameters.gazebo_attachment_frame =
    node.get_parameter("gazebo_attachment_frame").as_string();
  if (parameters.gazebo_attachment_frame.empty()) {
    parameters.gazebo_attachment_frame = parameters.hand_frame;
  }
  parameters.gazebo_attach_robot_model =
    node.get_parameter("gazebo_attach_robot_model").as_string();
  if (parameters.gazebo_attach_robot_model.empty()) {
    parameters.gazebo_attach_robot_model = "piper";
  }
  parameters.gazebo_attach_robot_link =
    node.get_parameter("gazebo_attach_robot_link").as_string();
  if (parameters.gazebo_attach_robot_link.empty()) {
    parameters.gazebo_attach_robot_link = "link6";
  }
  parameters.gazebo_attach_object_model =
    node.get_parameter("gazebo_attach_object_model").as_string();
  if (parameters.gazebo_attach_object_model.empty()) {
    parameters.gazebo_attach_object_model = parameters.pickup_object.id;
  }
  parameters.gazebo_attach_object_link =
    node.get_parameter("gazebo_attach_object_link").as_string();
  if (parameters.gazebo_attach_object_link.empty()) {
    parameters.gazebo_attach_object_link = "block_link";
  }
  parameters.tcp_offset = read_xyz_parameter(node, "tcp_offset_xyz");
  parameters.grasp_target_offset = read_xyz_parameter(node, "grasp_target_offset_xyz");
  parameters.pregrasp_offset = read_xyz_parameter(node, "pregrasp_offset_xyz");
  parameters.approach_direction = read_xyz_parameter(node, "approach_direction_xyz");
  parameters.lift_direction = read_xyz_parameter(node, "lift_direction_xyz");
  parameters.retreat_direction = read_xyz_parameter(node, "retreat_direction_xyz");
  parameters.grasp_orientation = read_rpy_parameter(node, "grasp_orientation_rpy");
  parameters.top_down_grasp_target_x_candidates =
    node.get_parameter("top_down_grasp_target_x_candidates").as_double_array();
  parameters.top_down_grasp_target_y_candidates =
    node.get_parameter("top_down_grasp_target_y_candidates").as_double_array();
  parameters.top_down_grasp_target_z_candidates =
    node.get_parameter("top_down_grasp_target_z_candidates").as_double_array();
  parameters.top_down_pregrasp_x_candidates =
    node.get_parameter("top_down_pregrasp_x_candidates").as_double_array();
  parameters.top_down_pregrasp_y_candidates =
    node.get_parameter("top_down_pregrasp_y_candidates").as_double_array();
  parameters.top_down_pregrasp_z_candidates =
    node.get_parameter("top_down_pregrasp_z_candidates").as_double_array();
  parameters.top_down_approach_direction_candidates =
    node.get_parameter("top_down_approach_direction_candidates").as_double_array();
  parameters.top_down_roll_candidates =
    node.get_parameter("top_down_roll_candidates").as_double_array();
  parameters.top_down_pitch_candidates =
    node.get_parameter("top_down_pitch_candidates").as_double_array();
  parameters.top_down_yaw_candidates =
    node.get_parameter("top_down_yaw_candidates").as_double_array();
  parameters.vision_target.enabled =
    node.get_parameter("vision_target.enabled").as_bool();
  parameters.vision_target.require_single_target =
    node.get_parameter("vision_target.require_single_target").as_bool();
  parameters.vision_target.require_valid_signal =
    node.get_parameter("vision_target.require_valid_signal").as_bool();
  parameters.vision_target.compute_grasp_offsets =
    node.get_parameter("vision_target.compute_grasp_offsets").as_bool();
  parameters.vision_target.lock_lateral_offsets_to_zero =
    node.get_parameter("vision_target.lock_lateral_offsets_to_zero").as_bool();
  parameters.vision_target.target_timeout_sec =
    node.get_parameter("vision_target.target_timeout_sec").as_double();
  parameters.vision_target.wait_after_home_timeout_sec =
    node.get_parameter("vision_target.wait_after_home_timeout_sec").as_double();
  parameters.vision_target.min_target_confidence =
    node.get_parameter("vision_target.min_target_confidence").as_double();
  parameters.vision_target.pregrasp_distance =
    node.get_parameter("vision_target.pregrasp_distance").as_double();
  parameters.vision_target.grasp_clearance =
    node.get_parameter("vision_target.grasp_clearance").as_double();
  parameters.vision_target.grasp_z_offset =
    node.get_parameter("vision_target.grasp_z_offset").as_double();
  parameters.vision_target.collision_scale_xy =
    node.get_parameter("vision_target.collision_scale_xy").as_double();
  parameters.vision_target.collision_scale_z =
    node.get_parameter("vision_target.collision_scale_z").as_double();
  parameters.vision_target.grasp_strategy =
    node.get_parameter("vision_target.grasp_strategy").as_string();
  parameters.vision_target.object_shape =
    node.get_parameter("vision_target.object_shape").as_string();
  parameters.vision_target.target_position_bias =
    read_xyz_parameter(node, "vision_target.target_position_bias_xyz");
  parameters.vision_target.default_target_size =
    read_xyz_parameter(node, "vision_target.default_target_size_xyz");
  parameters.vision_target.workspace_min =
    read_xyz_parameter(node, "vision_target.workspace_min_xyz");
  parameters.vision_target.workspace_max =
    read_xyz_parameter(node, "vision_target.workspace_max_xyz");
  parameters.vision_target.yaw_candidate_offsets =
    node.get_parameter("vision_target.yaw_candidate_offsets").as_double_array();
  parameters.vision_target.allowed_target_classes =
    node.get_parameter("vision_target.allowed_target_classes").as_string_array();
  parameters.observe_pose.enabled =
    node.get_parameter("observe_pose.enabled").as_bool();
  parameters.observe_pose.position =
    read_xyz_parameter(node, "observe_pose.xyz");
  parameters.observe_pose.orientation =
    read_rpy_parameter(node, "observe_pose.rpy");
  parameters.pre_place.enabled =
    node.get_parameter("pre_place.enabled").as_bool();
  parameters.pre_place.heading_offset =
    node.get_parameter("pre_place.heading_offset").as_double();
  parameters.pre_place.base_joint_name =
    node.get_parameter("pre_place.base_joint_name").as_string();
  if (parameters.pre_place.base_joint_name.empty()) {
    parameters.pre_place.base_joint_name = "joint1";
  }
  parameters.pre_place.min_delta =
    node.get_parameter("pre_place.min_delta").as_double();
  parameters.pre_place.coarse_base_first =
    node.get_parameter("pre_place.coarse_base_first").as_bool();
  parameters.pre_place.retract_joint3_name =
    node.get_parameter("pre_place.retract_joint3_name").as_string();
  if (parameters.pre_place.retract_joint3_name.empty()) {
    parameters.pre_place.retract_joint3_name = "joint3";
  }
  parameters.pre_place.retract_joint4_name =
    node.get_parameter("pre_place.retract_joint4_name").as_string();
  if (parameters.pre_place.retract_joint4_name.empty()) {
    parameters.pre_place.retract_joint4_name = "joint4";
  }
  parameters.pre_place.retract_joint3_delta =
    node.get_parameter("pre_place.retract_joint3_delta").as_double();
  parameters.pre_place.retract_joint4_delta =
    node.get_parameter("pre_place.retract_joint4_delta").as_double();
  parameters.pre_place.hover_after_base =
    node.get_parameter("pre_place.hover_after_base").as_bool();
  parameters.pre_place.hover_margin_xy =
    node.get_parameter("pre_place.hover_margin_xy").as_double();
  parameters.pre_place.hover_margin_z =
    node.get_parameter("pre_place.hover_margin_z").as_double();
  parameters.classification_place.enabled =
    node.get_parameter("classification_place.enabled").as_bool();
  parameters.classification_place.platform_slots =
    read_xyz_triples_parameter(node, "classification_place.platform_slots_xyz");
  parameters.classification_place.platform_slot_classes =
    node.get_parameter("classification_place.platform_slot_classes").as_string_array();
  parameters.classification_place.box_classes =
    node.get_parameter("classification_place.box_classes").as_string_array();
  parameters.classification_place.pregrasp_offset =
    read_xyz_parameter(node, "classification_place.pregrasp_offset_xyz");
  parameters.classification_place.lift_offset =
    read_xyz_parameter(node, "classification_place.lift_offset_xyz");
  parameters.classification_place.release_offset =
    read_xyz_parameter(node, "classification_place.release_offset_xyz");
  parameters.classification_place.grasp_orientation =
    read_rpy_parameter(node, "classification_place.grasp_orientation_rpy");
  parameters.classification_place.box_target_timeout_sec =
    node.get_parameter("classification_place.box_target_timeout_sec").as_double();
  parameters.classification_place.min_box_confidence =
    node.get_parameter("classification_place.min_box_confidence").as_double();
  parameters.classification_place.target_fusion_node_name =
    node.get_parameter("classification_place.target_fusion_node_name").as_string();
  if (parameters.classification_place.target_fusion_node_name.empty()) {
    parameters.classification_place.target_fusion_node_name = "/grasp_target_fusion";
  }
  parameters.classification_place.set_fusion_target_class =
    node.get_parameter("classification_place.set_fusion_target_class").as_bool();
  parameters.classification_place.target_switch_settle_sec =
    node.get_parameter("classification_place.target_switch_settle_sec").as_double();
  parameters.repeat_visual_pick.target_class =
    node.get_parameter("repeat_visual_pick.target_class").as_string();
  parameters.repeat_visual_pick.place_indices =
    node.get_parameter("repeat_visual_pick.place_indices").as_integer_array();
  parameters.repeat_visual_pick.target_fusion_node_name =
    node.get_parameter("repeat_visual_pick.target_fusion_node_name").as_string();
  if (parameters.repeat_visual_pick.target_fusion_node_name.empty()) {
    parameters.repeat_visual_pick.target_fusion_node_name = "/grasp_target_fusion";
  }
  parameters.repeat_visual_pick.set_fusion_target_class =
    node.get_parameter("repeat_visual_pick.set_fusion_target_class").as_bool();
  parameters.repeat_visual_pick.target_switch_settle_sec =
    node.get_parameter("repeat_visual_pick.target_switch_settle_sec").as_double();
  parameters.repeat_visual_pick.delay_between_picks_sec =
    node.get_parameter("repeat_visual_pick.delay_between_picks_sec").as_double();
  parameters.flame_tracking.set_enabled_service =
    node.get_parameter("flame_tracking.set_enabled_service").as_string();
  if (parameters.flame_tracking.set_enabled_service.empty()) {
    parameters.flame_tracking.set_enabled_service = "/flame_arm_tracker/set_enabled";
  }
  parameters.flame_tracking.service_timeout_sec =
    node.get_parameter("flame_tracking.service_timeout_sec").as_double();
  parameters.place_target.offset =
    read_xyz_parameter(node, "place_target.offset_xyz");
  parameters.place_target.release_height =
    node.get_parameter("place_target.release_height").as_double();
  parameters.place_target.orientation =
    read_rpy_parameter(node, "place_target.orientation_rpy");
  parameters.place_target.release_after_pre_place =
    node.get_parameter("place_target.release_after_pre_place").as_bool();
  parameters.place_target.allow_direct_release_fallback =
    node.get_parameter("place_target.allow_direct_release_fallback").as_bool();
  parameters.place_target.direct_release_retreat_z =
    node.get_parameter("place_target.direct_release_retreat_z").as_double();
  parameters.pickup_table = read_scene_box(
    node, "pickup_table", "pickup_table", parameters.planning_frame);
  parameters.place_bin = read_scene_open_top_bin(
    node, "place_bin", "rear_drop_bin", parameters.planning_frame);
  parameters.pickup_object = read_scene_cylinder(
    node, "pickup_object", "redbull_can", parameters.planning_frame);
  parameters.touch_links =
    node.get_parameter("pickup_object.touch_links").as_string_array();
  return parameters;
}

TaskFactory::TaskFactory(
  const rclcpp::Node::SharedPtr & node,
  const TaskParameters & parameters)
: node_(node), parameters_(parameters)
{
}

PlannerBundle TaskFactory::create_planners() const
{
  PlannerBundle planners;
  auto time_parameterization =
    std::make_shared<trajectory_processing::IterativeParabolicTimeParameterization>();

  planners.pipeline =
    std::make_shared<mtc::solvers::PipelinePlanner>(node_);
  planners.pipeline->setPlannerId(parameters_.pipeline_planner_id);
  planners.pipeline->setTimeParameterization(time_parameterization);

  planners.cartesian =
    std::make_shared<mtc::solvers::CartesianPath>();
  planners.cartesian->setStepSize(parameters_.cartesian_step_size);
  planners.cartesian->setJumpThreshold(parameters_.cartesian_jump_threshold);
  planners.cartesian->setMaxVelocityScalingFactor(
    parameters_.cartesian_velocity_scaling);
  planners.cartesian->setMaxAccelerationScalingFactor(
    parameters_.cartesian_acceleration_scaling);
  planners.cartesian->setTimeParameterization(time_parameterization);

  planners.interpolation =
    std::make_shared<mtc::solvers::JointInterpolationPlanner>();
  planners.interpolation->setTimeParameterization(time_parameterization);
  return planners;
}

void TaskFactory::configure_task_properties(mtc::Task & task) const
{
  task.loadRobotModel(node_);
  task.setProperty("group", parameters_.arm_group_name);
  task.setProperty("eef", parameters_.gripper_group_name);
  task.setProperty("ik_frame", parameters_.hand_frame);
}

mtc::Task TaskFactory::create_pick_task() const
{
  mtc::Task task;
  configure_task_properties(task);
  build_pick_task(task, parameters_, create_planners());
  return task;
}

mtc::Task TaskFactory::create_place_task() const
{
  mtc::Task task;
  configure_task_properties(task);
  build_place_task(task, parameters_, create_planners());
  return task;
}

mtc::Task TaskFactory::create_grasp_ik_probe_task() const
{
  mtc::Task task;
  configure_task_properties(task);
  build_grasp_ik_probe_task(task, parameters_, create_planners());
  return task;
}

mtc::Task TaskFactory::create_move_home_task() const
{
  mtc::Task task;
  configure_task_properties(task);
  task.stages()->setName("piper move home task");

  auto planners = create_planners();
  GripperStageBuilder gripper_stages(parameters_, planners.interpolation);

  auto current_state = std::make_unique<moveit::task_constructor::stages::CurrentState>(
    "current state");
  task.add(std::move(current_state));

  if (parameters_.move_home_open_gripper) {
    task.add(gripper_stages.open("open gripper"));
  }

  auto move_home = std::make_unique<moveit::task_constructor::stages::MoveTo>(
    "move arm home", planners.pipeline);
  move_home->setGroup(parameters_.arm_group_name);
  move_home->setGoal(parameters_.arm_home_named_target);
  task.add(std::move(move_home));

  return task;
}

}  // namespace piper_mtc_tasks
