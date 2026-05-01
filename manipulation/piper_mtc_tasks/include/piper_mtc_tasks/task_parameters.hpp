#pragma once

#include <string>
#include <vector>

#include <rclcpp/rclcpp.hpp>

namespace piper_mtc_tasks
{

struct XYZ
{
  double x{0.0};
  double y{0.0};
  double z{0.0};
};

struct RPY
{
  double roll{0.0};
  double pitch{0.0};
  double yaw{0.0};
};

struct SceneBox
{
  std::string id;
  std::string frame_id;
  XYZ center;
  XYZ size;
};

struct TaskParameters
{
  std::string action_name{"/manipulation/execute_task"};
  std::string planning_frame{"base_link"};
  std::string arm_group_name{"arm"};
  std::string gripper_group_name{"gripper"};
  std::string hand_frame{"gripper_grasp_center"};
  std::string arm_home_named_target{"zero"};
  std::string gripper_open_named_target{"open"};
  std::string gripper_close_named_target{"close"};
  std::string approach_direction_frame;
  std::string lift_direction_frame;
  std::string retreat_direction_frame;
  double gripper_open_joint7{-1.0};
  double gripper_close_joint7{-1.0};
  std::string pipeline_planner_id{"ompl"};
  int64_t max_solutions{1};
  int64_t max_ik_solutions{8};
  double min_solution_distance{1.0};
  double connect_timeout_sec{20.0};
  double plan_timeout_sec{30.0};
  double approach_min_distance{0.035};
  double approach_max_distance{0.055};
  double lift_min_distance{0.10};
  double lift_max_distance{0.18};
  double retreat_min_distance{0.02};
  double retreat_max_distance{0.06};
  double cartesian_step_size{0.005};
  double cartesian_jump_threshold{0.0};
  double cartesian_velocity_scaling{0.15};
  double cartesian_acceleration_scaling{0.10};
  double grasp_angle_delta{0.261799387799};
  bool execute_on_plan{true};
  bool diagnostic_ik_only{false};
  bool top_down_strategy_enabled{false};
  bool enable_gazebo_attachment{false};
  bool gazebo_attach_require_gripper_closed{true};
  int64_t autostart_task_type{0};
  double gazebo_attach_update_hz{30.0};
  double gazebo_attach_min_delay_sec{8.0};
  double gazebo_attach_max_distance{0.18};
  double gazebo_attach_max_horizontal_distance{0.08};
  double gazebo_attach_gripper_joint7_threshold{0.005};
  std::string gazebo_attachment_frame{"gripper_grasp_center"};
  std::string gazebo_attach_robot_model{"piper"};
  std::string gazebo_attach_robot_link{"link6"};
  std::string gazebo_attach_object_model{"pick_target_block"};
  std::string gazebo_attach_object_link{"block_link"};
  XYZ tcp_offset{-0.03136, -0.01342, 0.00441};
  XYZ grasp_target_offset{0.0, 0.0, 0.0};
  XYZ pregrasp_offset{0.0, 0.0, 0.05};
  XYZ approach_direction{0.0, 0.0, 1.0};
  XYZ lift_direction{0.0, 0.0, 1.0};
  XYZ retreat_direction{-1.0, 0.0, 0.0};
  RPY grasp_orientation{3.14159, 0.0, 0.0};
  std::vector<double> top_down_grasp_target_x_candidates;
  std::vector<double> top_down_grasp_target_y_candidates;
  std::vector<double> top_down_grasp_target_z_candidates;
  std::vector<double> top_down_pregrasp_x_candidates;
  std::vector<double> top_down_pregrasp_y_candidates;
  std::vector<double> top_down_pregrasp_z_candidates;
  std::vector<double> top_down_approach_direction_candidates;
  std::vector<double> top_down_roll_candidates;
  std::vector<double> top_down_pitch_candidates;
  std::vector<double> top_down_yaw_candidates;
  SceneBox pickup_stand;
  SceneBox place_stand;
  SceneBox pickup_block;
  std::vector<std::string> touch_links;
};

void declare_task_parameters(rclcpp::Node & node);
TaskParameters load_task_parameters(rclcpp::Node & node);

}  // namespace piper_mtc_tasks
