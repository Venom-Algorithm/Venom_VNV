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
  node.declare_parameter<bool>("top_down_strategy_enabled", false);
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
    "pickup_block.touch_links",
    std::vector<std::string>{"link7", "link8"});

  node.declare_parameter<std::string>("pickup_stand.id", "pickup_stand_box");
  node.declare_parameter<double>("pickup_stand.x", 0.281);
  node.declare_parameter<double>("pickup_stand.y", 0.0);
  node.declare_parameter<double>("pickup_stand.z", 0.423);
  node.declare_parameter<double>("pickup_stand.size_x", 0.22);
  node.declare_parameter<double>("pickup_stand.size_y", 0.18);
  node.declare_parameter<double>("pickup_stand.size_z", 0.02);

  node.declare_parameter<std::string>("place_stand.id", "place_stand_box");
  node.declare_parameter<double>("place_stand.x", -0.02);
  node.declare_parameter<double>("place_stand.y", 0.38);
  node.declare_parameter<double>("place_stand.z", 0.423);
  node.declare_parameter<double>("place_stand.size_x", 0.22);
  node.declare_parameter<double>("place_stand.size_y", 0.18);
  node.declare_parameter<double>("place_stand.size_z", 0.02);

  node.declare_parameter<std::string>("pickup_block.id", "pick_target_block");
  node.declare_parameter<double>("pickup_block.x", 0.281);
  node.declare_parameter<double>("pickup_block.y", 0.0);
  node.declare_parameter<double>("pickup_block.z", 0.4505);
  node.declare_parameter<double>("pickup_block.size_x", 0.018);
  node.declare_parameter<double>("pickup_block.size_y", 0.018);
  node.declare_parameter<double>("pickup_block.size_z", 0.035);
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
  parameters.top_down_strategy_enabled =
    node.get_parameter("top_down_strategy_enabled").as_bool();
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
    parameters.gazebo_attach_object_model = parameters.pickup_block.id;
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
  parameters.pickup_stand = read_scene_box(
    node, "pickup_stand", "pickup_stand_box", parameters.planning_frame);
  parameters.place_stand = read_scene_box(
    node, "place_stand", "place_stand_box", parameters.planning_frame);
  parameters.pickup_block = read_scene_box(
    node, "pickup_block", "pick_target_block", parameters.planning_frame);
  parameters.touch_links =
    node.get_parameter("pickup_block.touch_links").as_string_array();
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

  task.add(gripper_stages.open("open gripper"));

  auto move_home = std::make_unique<moveit::task_constructor::stages::MoveTo>(
    "move arm home", planners.pipeline);
  move_home->setGroup(parameters_.arm_group_name);
  move_home->setGoal(parameters_.arm_home_named_target);
  task.add(std::move(move_home));

  return task;
}

}  // namespace piper_mtc_tasks
