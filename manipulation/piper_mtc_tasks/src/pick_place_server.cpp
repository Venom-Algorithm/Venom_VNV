#include <algorithm>
#include <chrono>
#include <cmath>
#include <cctype>
#include <future>
#include <iomanip>
#include <memory>
#include <mutex>
#include <optional>
#include <sstream>
#include <string>
#include <thread>
#include <vector>

#include <tf2/LinearMath/Matrix3x3.h>
#include <tf2/LinearMath/Quaternion.h>
#include <moveit/collision_detection/collision_common.h>
#include <moveit/robot_model/joint_model.h>
#include <moveit/robot_trajectory/robot_trajectory.h>
#include <moveit/robot_state/robot_state.h>
#include <moveit/planning_scene/planning_scene.h>
#include <moveit/task_constructor/stage.h>
#include <moveit/task_constructor/storage.h>
#include <moveit/task_constructor/task.h>
#include <moveit/trajectory_processing/iterative_time_parameterization.h>
#include <moveit/move_group_interface/move_group_interface.h>
#include <moveit_task_constructor_msgs/msg/solution.hpp>
#include <moveit_msgs/msg/move_it_error_codes.hpp>
#include <geometry_msgs/msg/pose.hpp>
#include <geometry_msgs/msg/pose_stamped.hpp>
#if defined(HAVE_LINKATTACHER_MSGS)
#include <linkattacher_msgs/srv/attach_link.hpp>
#include <linkattacher_msgs/srv/detach_link.hpp>
#endif
#include <rclcpp/rclcpp.hpp>
#include <rclcpp/parameter_client.hpp>
#include <rclcpp_action/rclcpp_action.hpp>
#include <sensor_msgs/msg/joint_state.hpp>
#include <std_msgs/msg/bool.hpp>
#include <trajectory_msgs/msg/joint_trajectory.hpp>
#include <trajectory_msgs/msg/joint_trajectory_point.hpp>

#include <venom_manipulation_interfaces/action/execute_task.hpp>
#include <venom_manipulation_interfaces/msg/grasp_target.hpp>

#include "piper_mtc_tasks/scene_manager.hpp"
#include "piper_mtc_tasks/stage_builders.hpp"
#include "piper_mtc_tasks/task_factory.hpp"

namespace piper_mtc_tasks
{

namespace
{

double choose_nearest_bounded_angle(
  double current_angle,
  double desired_angle,
  const moveit::core::VariableBounds & bounds)
{
  double best_angle = desired_angle;
  double best_distance = std::numeric_limits<double>::infinity();

  for (int wraps = -1; wraps <= 1; ++wraps) {
    const double candidate = desired_angle + static_cast<double>(wraps) * 2.0 * M_PI;
    if (bounds.position_bounded_) {
      if (candidate < bounds.min_position_ || candidate > bounds.max_position_) {
        continue;
      }
    }

    const double distance = std::abs(candidate - current_angle);
    if (distance < best_distance) {
      best_distance = distance;
      best_angle = candidate;
    }
  }

  if (!std::isfinite(best_distance)) {
    best_angle = std::min(std::max(desired_angle, bounds.min_position_), bounds.max_position_);
  }

  return best_angle;
}

double normalize_angle(double angle)
{
  while (angle > M_PI) {
    angle -= 2.0 * M_PI;
  }
  while (angle < -M_PI) {
    angle += 2.0 * M_PI;
  }
  return angle;
}

double positive_or(double value, double fallback)
{
  return value > 1e-6 ? value : fallback;
}

bool has_cartesian_distance(double min_distance, double max_distance)
{
  constexpr double kDistanceEpsilon = 1e-6;
  return std::abs(min_distance) > kDistanceEpsilon ||
         std::abs(max_distance) > kDistanceEpsilon;
}

std::vector<double> make_single_candidate(double value)
{
  return std::vector<double>{value};
}

void append_unique_angle_candidate(std::vector<double> & candidates, double angle)
{
  constexpr double kAngleTolerance = 1e-6;
  const double normalized_angle = normalize_angle(angle);
  const auto existing = std::find_if(
    candidates.begin(),
    candidates.end(),
    [normalized_angle](double candidate) {
      return std::abs(normalize_angle(candidate - normalized_angle)) < kAngleTolerance;
    });
  if (existing == candidates.end()) {
    candidates.push_back(normalized_angle);
  }
}

double choose_good_enough_object_angle(
  double current_object_angle,
  double object_radius_from_base,
  const SceneOpenTopBin & bin,
  double object_radius)
{
  (void)current_object_angle;
  (void)object_radius_from_base;
  (void)object_radius;

  // For coarse pre-place rotation, prioritize pointing the carried object toward the
  // bin center direction instead of rotating all the way to an "inside-bin optimal"
  // angle. This keeps joint1 from overshooting when a simple release is enough.
  return std::atan2(bin.center.y, bin.center.x);
}

std::string normalize_class_name(const std::string & value)
{
  std::string normalized;
  normalized.reserve(value.size());
  for (const char character : value) {
    normalized.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(character))));
  }
  return normalized;
}

std::string describe_bounds_violations(
  const moveit::core::RobotState & state,
  const std::string & label)
{
  constexpr double kTolerance = 1e-9;
  std::ostringstream out;
  bool any_violation = false;

  const auto & variable_names = state.getVariableNames();
  const auto & robot_model = state.getRobotModel();
  for (const auto & variable_name : variable_names) {
    const auto & bounds = robot_model->getVariableBounds(variable_name);
    if (!bounds.position_bounded_) {
      continue;
    }

    const double value = state.getVariablePosition(variable_name);
    const bool below = value < bounds.min_position_ - kTolerance;
    const bool above = value > bounds.max_position_ + kTolerance;
    if (!below && !above) {
      continue;
    }

    if (!any_violation) {
      out << label << " bounds violations:";
      any_violation = true;
    }

    out << "\n  " << variable_name << " = " << std::fixed << std::setprecision(9) << value
        << " outside [" << bounds.min_position_ << ", " << bounds.max_position_ << "]";
  }

  if (!any_violation) {
    out << label << " has no strict position bounds violations.";
  }
  return out.str();
}

bool has_bounds_violation(const moveit::core::RobotState & state)
{
  constexpr double kTolerance = 1e-9;
  const auto & variable_names = state.getVariableNames();
  const auto & robot_model = state.getRobotModel();
  for (const auto & variable_name : variable_names) {
    const auto & bounds = robot_model->getVariableBounds(variable_name);
    if (!bounds.position_bounded_) {
      continue;
    }

    const double value = state.getVariablePosition(variable_name);
    if (value < bounds.min_position_ - kTolerance ||
      value > bounds.max_position_ + kTolerance)
    {
      return true;
    }
  }
  return false;
}

std::string describe_solution_state_bounds(
  const mtc::SolutionBase & solution,
  const std::string & prefix)
{
  std::ostringstream out;
  if (solution.start() != nullptr && solution.start()->scene()) {
    out << describe_bounds_violations(
      solution.start()->scene()->getCurrentState(),
      prefix + " start");
  } else {
    out << prefix << " start scene unavailable.";
  }

  out << '\n';

  if (solution.end() != nullptr && solution.end()->scene()) {
    out << describe_bounds_violations(
      solution.end()->scene()->getCurrentState(),
      prefix + " end");
  } else {
    out << prefix << " end scene unavailable.";
  }
  return out.str();
}

std::string describe_collisions(
  const planning_scene::PlanningScene & scene,
  const moveit::core::RobotState & state,
  const std::string & label)
{
  collision_detection::CollisionRequest request;
  collision_detection::CollisionResult result;
  request.contacts = true;
  request.max_contacts = 20;
  request.max_contacts_per_pair = 3;

  scene.checkCollision(request, result, state);
  if (!result.collision) {
    return label + " has no collision contacts.";
  }

  std::ostringstream out;
  out << label << " collision contacts:";
  for (const auto & contact_pair : result.contacts) {
    out << "\n  " << contact_pair.first.first << " <-> " << contact_pair.first.second
        << " count=" << contact_pair.second.size();
  }
  return out.str();
}

std::string describe_solution_state_collisions(
  const mtc::SolutionBase & solution,
  const std::string & prefix)
{
  std::ostringstream out;
  if (solution.start() != nullptr && solution.start()->scene()) {
    const auto & scene = *solution.start()->scene();
    out << describe_collisions(scene, scene.getCurrentState(), prefix + " start");
  } else {
    out << prefix << " start scene unavailable.";
  }

  out << '\n';

  if (solution.end() != nullptr && solution.end()->scene()) {
    const auto & scene = *solution.end()->scene();
    out << describe_collisions(scene, scene.getCurrentState(), prefix + " end");
  } else {
    out << prefix << " end scene unavailable.";
  }
  return out.str();
}

void append_solution_tree(
  const mtc::SolutionBase & solution,
  std::ostringstream & out,
  std::size_t depth)
{
  const std::string indent(depth * 2, ' ');
  const auto * creator = solution.creator();
  out << indent
      << "stage='" << (creator != nullptr ? creator->name() : "<unknown>") << "'";
  if (!solution.comment().empty()) {
    out << " comment='" << solution.comment() << "'";
  }
  out << '\n';

  if (const auto * sequence = dynamic_cast<const mtc::SolutionSequence *>(&solution)) {
    for (const auto * child_solution : sequence->solutions()) {
      if (child_solution == nullptr) {
        continue;
      }
      append_solution_tree(*child_solution, out, depth + 1);
    }
  } else if (const auto * wrapped = dynamic_cast<const mtc::WrappedSolution *>(&solution)) {
    if (wrapped->wrapped() != nullptr) {
      append_solution_tree(*wrapped->wrapped(), out, depth + 1);
    }
  }
}

std::string describe_solution_tree(const mtc::SolutionBase & solution)
{
  std::ostringstream out;
  append_solution_tree(solution, out, 0);
  return out.str();
}

void log_stage_solution_bounds(
  const rclcpp::Logger & logger,
  const mtc::Task & task)
{
  task.stages()->traverseRecursively(
    [&logger](const mtc::Stage & stage, unsigned int) {
      std::size_t solution_index = 0;
      for (const auto & solution : stage.solutions()) {
        if (!solution) {
          continue;
        }

        const bool start_invalid =
          solution->start() != nullptr &&
          solution->start()->scene() &&
          has_bounds_violation(solution->start()->scene()->getCurrentState());
        const bool end_invalid =
          solution->end() != nullptr &&
          solution->end()->scene() &&
          has_bounds_violation(solution->end()->scene()->getCurrentState());
        if (start_invalid || end_invalid) {
          RCLCPP_ERROR_STREAM(
            logger,
            "MTC stage solution bounds issue: stage='" << stage.name()
                                                       << "' solution=" << solution_index
                                                       << '\n'
                                                       << describe_solution_state_bounds(
                                                         *solution,
                                                         stage.name() + " solution " +
                                                         std::to_string(solution_index)));
        }
        ++solution_index;
      }

      std::size_t failure_index = 0;
      for (const auto & failure : stage.failures()) {
        if (!failure) {
          continue;
        }

        RCLCPP_ERROR_STREAM(
          logger,
          "MTC stored failure: stage='" << stage.name()
                                       << "' failure=" << failure_index
                                       << " comment='" << failure->comment() << "'\n"
                                       << describe_solution_state_bounds(
                                         *failure,
                                         stage.name() + " failure " +
                                         std::to_string(failure_index))
                                       << '\n'
                                       << describe_solution_state_collisions(
                                         *failure,
                                         stage.name() + " failure " +
                                         std::to_string(failure_index)));
        ++failure_index;
      }

      return true;
    });
}

double duration_to_seconds(const builtin_interfaces::msg::Duration & duration)
{
  return static_cast<double>(duration.sec) + static_cast<double>(duration.nanosec) * 1e-9;
}

void log_solution_trajectory_timing(
  const rclcpp::Logger & logger,
  const mtc::SolutionBase & solution,
  mtc::Introspection * introspection)
{
  moveit_task_constructor_msgs::msg::Solution message;
  solution.toMsg(message, introspection);

  std::size_t index = 0;
  for (const auto & sub_trajectory : message.sub_trajectory) {
    const auto & joint_trajectory = sub_trajectory.trajectory.joint_trajectory;
    const auto point_count = joint_trajectory.points.size();
    if (point_count == 0) {
      RCLCPP_INFO_STREAM(
        logger,
        "MTC trajectory timing: sub=" << index
                                      << " stage_id=" << sub_trajectory.info.stage_id
                                      << " planner='" << sub_trajectory.info.planner_id
                                      << "' joints=[] points=0");
      ++index;
      continue;
    }

    const double first_time =
      duration_to_seconds(joint_trajectory.points.front().time_from_start);
    const double last_time =
      duration_to_seconds(joint_trajectory.points.back().time_from_start);

    bool strictly_increasing = true;
    double previous_time = first_time;
    for (std::size_t point_index = 1; point_index < point_count; ++point_index) {
      const double time =
        duration_to_seconds(joint_trajectory.points[point_index].time_from_start);
      if (time <= previous_time) {
        strictly_increasing = false;
        break;
      }
      previous_time = time;
    }

    RCLCPP_INFO_STREAM(
      logger,
      "MTC trajectory timing: sub=" << index
                                    << " stage_id=" << sub_trajectory.info.stage_id
                                    << " planner='" << sub_trajectory.info.planner_id
                                    << "' joints="
                                    << joint_trajectory.joint_names.size()
                                    << " points=" << point_count
                                    << " first=" << first_time
                                    << " last=" << last_time
                                    << " increasing="
                                    << (strictly_increasing ? "true" : "false"));
    ++index;
  }
}

bool trajectory_has_strictly_increasing_timing(
  const robot_trajectory::RobotTrajectory & trajectory)
{
  const std::size_t waypoint_count = trajectory.getWayPointCount();
  if (waypoint_count < 2) {
    return true;
  }

  double previous_time = trajectory.getWayPointDurationFromStart(0);
  for (std::size_t waypoint_index = 1; waypoint_index < waypoint_count; ++waypoint_index) {
    const double time = trajectory.getWayPointDurationFromStart(waypoint_index);
    if (time <= previous_time) {
      return false;
    }
    previous_time = time;
  }
  return true;
}

std::size_t retime_solution_trajectories(
  mtc::SolutionBase & solution,
  const trajectory_processing::TimeParameterization & time_parameterization,
  double velocity_scaling,
  double acceleration_scaling)
{
  if (auto * sub_trajectory = dynamic_cast<mtc::SubTrajectory *>(&solution)) {
    const auto original_trajectory = sub_trajectory->trajectory();
    if (
      !original_trajectory ||
      original_trajectory->getWayPointCount() < 2 ||
      trajectory_has_strictly_increasing_timing(*original_trajectory))
    {
      return 0;
    }

    auto retimed_trajectory =
      std::make_shared<robot_trajectory::RobotTrajectory>(*original_trajectory, true);
    if (!time_parameterization.computeTimeStamps(
        *retimed_trajectory,
        velocity_scaling,
        acceleration_scaling))
    {
      return 0;
    }

    sub_trajectory->setTrajectory(retimed_trajectory);
    return 1;
  }

  std::size_t retimed_count = 0;
  if (auto * sequence = dynamic_cast<mtc::SolutionSequence *>(&solution)) {
    for (const auto * child_solution : sequence->solutions()) {
      if (child_solution == nullptr) {
        continue;
      }
      retimed_count += retime_solution_trajectories(
        *const_cast<mtc::SolutionBase *>(child_solution),
        time_parameterization,
        velocity_scaling,
        acceleration_scaling);
    }
  } else if (auto * wrapped = dynamic_cast<mtc::WrappedSolution *>(&solution)) {
    if (wrapped->wrapped() != nullptr) {
      retimed_count += retime_solution_trajectories(
        *const_cast<mtc::SolutionBase *>(wrapped->wrapped()),
        time_parameterization,
        velocity_scaling,
        acceleration_scaling);
    }
  }

  return retimed_count;
}

struct ExecutableTrajectoryStep
{
  std::string stage_name;
  moveit_msgs::msg::RobotTrajectory trajectory;
};

void collect_executable_trajectory_steps(
  const mtc::SolutionBase & solution,
  std::vector<ExecutableTrajectoryStep> & steps)
{
  if (const auto * sub_trajectory = dynamic_cast<const mtc::SubTrajectory *>(&solution)) {
    const auto trajectory = sub_trajectory->trajectory();
    if (trajectory && trajectory->getWayPointCount() > 0) {
      ExecutableTrajectoryStep step;
      step.stage_name = sub_trajectory->creator() != nullptr ?
        sub_trajectory->creator()->name() :
        "<unknown>";
      trajectory->getRobotTrajectoryMsg(step.trajectory);
      steps.push_back(std::move(step));
    }
    return;
  }

  if (const auto * sequence = dynamic_cast<const mtc::SolutionSequence *>(&solution)) {
    for (const auto * child_solution : sequence->solutions()) {
      if (child_solution != nullptr) {
        collect_executable_trajectory_steps(*child_solution, steps);
      }
    }
    return;
  }

  if (const auto * wrapped = dynamic_cast<const mtc::WrappedSolution *>(&solution)) {
    if (wrapped->wrapped() != nullptr) {
      collect_executable_trajectory_steps(*wrapped->wrapped(), steps);
    }
  }
}

bool stage_name_contains(const std::string & stage_name, const std::string & token)
{
  return stage_name.find(token) != std::string::npos;
}

bool trajectory_targets_gripper(const moveit_msgs::msg::RobotTrajectory & trajectory)
{
  for (const auto & joint_name : trajectory.joint_trajectory.joint_names) {
    if (joint_name == "joint7" || joint_name == "joint8") {
      return true;
    }
  }
  return false;
}

uint8_t feedback_stage_for_step(const std::string & stage_name)
{
  if (stage_name_contains(stage_name, "home")) {
    return venom_manipulation_interfaces::action::ExecuteTask::Goal::STAGE_MOVING_HOME;
  }
  if (stage_name_contains(stage_name, "place")) {
    return venom_manipulation_interfaces::action::ExecuteTask::Goal::STAGE_MOVING_PLACE;
  }
  if (stage_name_contains(stage_name, "open gripper")) {
    return venom_manipulation_interfaces::action::ExecuteTask::Goal::STAGE_OPENING_GRIPPER;
  }
  if (stage_name_contains(stage_name, "close gripper")) {
    return venom_manipulation_interfaces::action::ExecuteTask::Goal::STAGE_CLOSING_GRIPPER;
  }
  if (stage_name_contains(stage_name, "lift")) {
    return venom_manipulation_interfaces::action::ExecuteTask::Goal::STAGE_LIFTING;
  }
  if (stage_name_contains(stage_name, "grasp")) {
    return venom_manipulation_interfaces::action::ExecuteTask::Goal::STAGE_MOVING_GRASP;
  }
  return venom_manipulation_interfaces::action::ExecuteTask::Goal::STAGE_MOVING_PREGRASP;
}

}  // namespace

class PickPlaceServer : public rclcpp::Node
{
public:
  using ExecuteTask = venom_manipulation_interfaces::action::ExecuteTask;
  using GraspTarget = venom_manipulation_interfaces::msg::GraspTarget;
#if defined(HAVE_LINKATTACHER_MSGS)
  using AttachLink = linkattacher_msgs::srv::AttachLink;
  using DetachLink = linkattacher_msgs::srv::DetachLink;
#endif
  using GoalHandleExecuteTask = rclcpp_action::ServerGoalHandle<ExecuteTask>;

  PickPlaceServer()
  : Node("pick_place_server")
  {
    declare_task_parameters(*this);
    parameters_ = load_task_parameters(*this);
    auto node_handle = rclcpp::Node::SharedPtr(this, [](rclcpp::Node *) {});
    factory_ = std::make_unique<TaskFactory>(node_handle, parameters_);
    scene_manager_ = std::make_unique<SceneManager>(get_logger());
    target_fusion_parameter_client_ = std::make_shared<rclcpp::AsyncParametersClient>(
      this,
      parameters_.classification_place.target_fusion_node_name);
    arm_move_group_ = std::make_unique<moveit::planning_interface::MoveGroupInterface>(
      node_handle, parameters_.arm_group_name);
    gripper_move_group_ = std::make_unique<moveit::planning_interface::MoveGroupInterface>(
      node_handle, parameters_.gripper_group_name);
    arm_move_group_->setPoseReferenceFrame(parameters_.planning_frame);
    arm_move_group_->setPlanningTime(parameters_.plan_timeout_sec);
    arm_move_group_->setMaxVelocityScalingFactor(parameters_.cartesian_velocity_scaling);
    arm_move_group_->setMaxAccelerationScalingFactor(parameters_.cartesian_acceleration_scaling);
    if (!parameters_.hand_frame.empty() && !arm_move_group_->setEndEffectorLink(parameters_.hand_frame)) {
      RCLCPP_WARN(
        get_logger(),
        "Failed to set arm end effector link to '%s'; explicit lift will query the link by name instead",
        parameters_.hand_frame.c_str());
    }
    action_callback_group_ =
      create_callback_group(rclcpp::CallbackGroupType::Reentrant);
    gazebo_callback_group_ =
      create_callback_group(rclcpp::CallbackGroupType::Reentrant);

    if (parameters_.enable_gazebo_attachment) {
#if defined(HAVE_LINKATTACHER_MSGS)
      gazebo_attach_link_client_ = create_client<AttachLink>(
        "/ATTACHLINK",
        rmw_qos_profile_services_default,
        gazebo_callback_group_);
      gazebo_detach_link_client_ = create_client<DetachLink>(
        "/DETACHLINK",
        rmw_qos_profile_services_default,
        gazebo_callback_group_);
#else
      RCLCPP_WARN(
        get_logger(),
        "Gazebo attachment requested, but linkattacher_msgs is unavailable. Disabling gazebo attachment support.");
      parameters_.enable_gazebo_attachment = false;
#endif
    }

    rclcpp::SubscriptionOptions joint_state_options;
    joint_state_options.callback_group = gazebo_callback_group_;
    joint_state_subscription_ = create_subscription<sensor_msgs::msg::JointState>(
      "/joint_states",
      rclcpp::SensorDataQoS(),
      std::bind(&PickPlaceServer::handle_joint_state, this, std::placeholders::_1),
      joint_state_options);
    grasp_target_subscription_ = create_subscription<GraspTarget>(
      "/perception/grasp_target",
      rclcpp::SensorDataQoS(),
      std::bind(&PickPlaceServer::handle_grasp_target, this, std::placeholders::_1));
    target_valid_subscription_ = create_subscription<std_msgs::msg::Bool>(
      "/perception/target_valid",
      10,
      std::bind(&PickPlaceServer::handle_target_valid, this, std::placeholders::_1));

    action_server_ = rclcpp_action::create_server<ExecuteTask>(
      this,
      parameters_.action_name,
      std::bind(&PickPlaceServer::handle_goal, this, std::placeholders::_1, std::placeholders::_2),
      std::bind(&PickPlaceServer::handle_cancel, this, std::placeholders::_1),
      std::bind(&PickPlaceServer::handle_accepted, this, std::placeholders::_1),
      rcl_action_server_get_default_options(),
      action_callback_group_);

    if (parameters_.autostart_task_type > 0) {
      autostart_timer_ = create_wall_timer(
        std::chrono::seconds(2),
        std::bind(&PickPlaceServer::run_autostart_task, this));
    }

    RCLCPP_INFO(
      get_logger(),
      "MTC pick_place_server ready on '%s' for arm group '%s' and gripper group '%s'",
      parameters_.action_name.c_str(),
      parameters_.arm_group_name.c_str(),
      parameters_.gripper_group_name.c_str());
  }

private:
  rclcpp_action::GoalResponse handle_goal(
    const rclcpp_action::GoalUUID &,
    std::shared_ptr<const ExecuteTask::Goal> goal)
  {
    if (goal->task_type != ExecuteTask::Goal::PICK_AND_PLACE_FIXED &&
      goal->task_type != ExecuteTask::Goal::MOVE_HOME &&
      goal->task_type != ExecuteTask::Goal::MOVE_OBSERVE &&
      goal->task_type != ExecuteTask::Goal::PICK_AND_PLACE_LATEST_TARGET &&
      goal->task_type != ExecuteTask::Goal::CLASSIFY_PLATFORM_TO_COLOR_BOXES)
    {
      RCLCPP_WARN(get_logger(), "Rejecting unsupported task type %u", goal->task_type);
      return rclcpp_action::GoalResponse::REJECT;
    }

    std::lock_guard<std::mutex> lock(current_task_mutex_);
    if (active_goal_) {
      RCLCPP_WARN(get_logger(), "Rejecting task type %u because another MTC task is active", goal->task_type);
      return rclcpp_action::GoalResponse::REJECT;
    }
    active_goal_ = true;
    return rclcpp_action::GoalResponse::ACCEPT_AND_EXECUTE;
  }

  rclcpp_action::CancelResponse handle_cancel(
    const std::shared_ptr<GoalHandleExecuteTask>)
  {
    RCLCPP_INFO(get_logger(), "Cancel requested");
    std::lock_guard<std::mutex> lock(current_task_mutex_);
    if (current_task_ != nullptr) {
      current_task_->preempt();
      RCLCPP_INFO(get_logger(), "Forwarded cancel request to current MTC task");
    }
    return rclcpp_action::CancelResponse::ACCEPT;
  }

  void handle_accepted(const std::shared_ptr<GoalHandleExecuteTask> goal_handle)
  {
    std::thread(
      [this, goal_handle]() {
        execute_goal(goal_handle);
      }).detach();
  }

  void publish_feedback(
    const std::shared_ptr<GoalHandleExecuteTask> & goal_handle,
    uint8_t stage,
    const std::string & message)
  {
    auto feedback = std::make_shared<ExecuteTask::Feedback>();
    feedback->current_stage = stage;
    feedback->message = message;
    goal_handle->publish_feedback(feedback);
  }

  void finish_result(
    const std::shared_ptr<GoalHandleExecuteTask> & goal_handle,
    bool success,
    uint8_t stage_reached,
    int32_t error_code,
    const std::string & message)
  {
    auto result = std::make_shared<ExecuteTask::Result>();
    result->success = success;
    result->stage_reached = stage_reached;
    result->error_code = error_code;
    result->message = message;

    if (success) {
      goal_handle->succeed(result);
    } else if (goal_handle->is_canceling()) {
      goal_handle->canceled(result);
    } else {
      goal_handle->abort(result);
    }
  }

  void execute_goal(const std::shared_ptr<GoalHandleExecuteTask> & goal_handle)
  {
    const auto task_type = goal_handle->get_goal()->task_type;
    const bool move_home_task = task_type == ExecuteTask::Goal::MOVE_HOME;
    const bool observe_task = task_type == ExecuteTask::Goal::MOVE_OBSERVE;
    const bool vision_pick_task = task_type == ExecuteTask::Goal::PICK_AND_PLACE_LATEST_TARGET;
    const bool classification_task =
      task_type == ExecuteTask::Goal::CLASSIFY_PLATFORM_TO_COLOR_BOXES;
    const bool pick_task =
      task_type == ExecuteTask::Goal::PICK_AND_PLACE_FIXED || vision_pick_task;
    const bool diagnostic_ik_only = pick_task && parameters_.diagnostic_ik_only;

    try {
      if (observe_task) {
        execute_observe_goal(goal_handle);
        return;
      }

      if (classification_task) {
        execute_classification_place_goal(goal_handle);
        return;
      }

      const auto baseline_parameters = parameters_;
      if (pick_task && parameters_.move_home_before_pick) {
        publish_feedback(
          goal_handle,
          ExecuteTask::Goal::STAGE_MOVING_HOME,
          "Moving arm home before pick");

        std::string home_error_message;
        if (!execute_named_arm_target(
            parameters_.arm_home_named_target,
            "home before pick",
            home_error_message))
        {
          finish_result(
            goal_handle,
            false,
            ExecuteTask::Goal::STAGE_MOVING_HOME,
            ExecuteTask::Result::ERROR_EXECUTION_FAILED,
            home_error_message.empty() ?
            "Failed to move arm home before pick." :
            home_error_message);
          clear_current_task(nullptr);
          return;
        }

        if (vision_pick_task && parameters_.vision_target.wait_after_home_timeout_sec > 0.0) {
          publish_feedback(
            goal_handle,
            ExecuteTask::Goal::STAGE_WAITING_FOR_TARGET,
            "Waiting for a fresh visual target after home");

          std::string fresh_target_error_message;
          if (!wait_for_visual_target_after(
              now(),
              parameters_.vision_target.wait_after_home_timeout_sec,
              fresh_target_error_message))
          {
            finish_result(
              goal_handle,
              false,
              ExecuteTask::Goal::STAGE_WAITING_FOR_TARGET,
              ExecuteTask::Result::ERROR_NOT_READY,
              fresh_target_error_message);
            clear_current_task(nullptr);
            return;
          }
        }
      }

      if (vision_pick_task) {
        publish_feedback(
          goal_handle,
          ExecuteTask::Goal::STAGE_WAITING_FOR_TARGET,
          "Resolving latest visual grasp target");

        std::string target_error_message;
        if (!prepare_visual_pick_target(target_error_message)) {
          finish_result(
            goal_handle,
            false,
            ExecuteTask::Goal::STAGE_WAITING_FOR_TARGET,
            ExecuteTask::Result::ERROR_NOT_READY,
            target_error_message);
          clear_current_task(nullptr);
          return;
        }

        if (parameters_.pick_only && parameters_.use_direct_visual_pick_fallback) {
          std::string direct_pick_error_message;
          if (execute_direct_visual_pick(goal_handle, direct_pick_error_message)) {
            parameters_ = baseline_parameters;
            auto node_handle = rclcpp::Node::SharedPtr(this, [](rclcpp::Node *) {});
            factory_ = std::make_unique<TaskFactory>(node_handle, parameters_);
            clear_current_task(nullptr);
            finish_result(
              goal_handle,
              true,
              ExecuteTask::Goal::STAGE_DONE,
              ExecuteTask::Result::ERROR_NONE,
              "Direct visual pick completed.");
          } else {
            parameters_ = baseline_parameters;
            auto node_handle = rclcpp::Node::SharedPtr(this, [](rclcpp::Node *) {});
            factory_ = std::make_unique<TaskFactory>(node_handle, parameters_);
            clear_current_task(nullptr);
            finish_result(
              goal_handle,
              false,
              ExecuteTask::Goal::STAGE_FAILED,
              ExecuteTask::Result::ERROR_EXECUTION_FAILED,
              direct_pick_error_message.empty() ?
              "Direct visual pick failed." :
              direct_pick_error_message);
          }
          return;
        }
      }

      publish_feedback(
        goal_handle,
        move_home_task ?
        ExecuteTask::Goal::STAGE_MOVING_HOME :
        ExecuteTask::Goal::STAGE_MOVING_PREGRASP,
        "Building MTC task");

      mtc::Task task =
        move_home_task ?
        factory_->create_move_home_task() :
        diagnostic_ik_only ?
        factory_->create_grasp_ik_probe_task() :
        factory_->create_pick_task();
      set_current_task(&task);

      if (pick_task) {
        detach_pick_object_from_moveit();
      }

      if (pick_task && !parameters_.disable_scene_objects && !scene_manager_->sync_pick_scene(parameters_))
      {
        parameters_ = baseline_parameters;
        auto node_handle = rclcpp::Node::SharedPtr(this, [](rclcpp::Node *) {});
        factory_ = std::make_unique<TaskFactory>(node_handle, parameters_);
        clear_current_task(&task);
        finish_result(
          goal_handle,
          false,
          ExecuteTask::Goal::STAGE_FAILED,
          ExecuteTask::Result::ERROR_EXECUTION_FAILED,
          "Failed to synchronize pick scene before MTC planning.");
        return;
      }

      try {
        task.init();
      } catch (const mtc::InitStageException & exception) {
        std::ostringstream message;
        message << exception;
        RCLCPP_ERROR_STREAM(get_logger(), "MTC init failed:\n" << message.str());
        parameters_ = baseline_parameters;
        auto node_handle = rclcpp::Node::SharedPtr(this, [](rclcpp::Node *) {});
        factory_ = std::make_unique<TaskFactory>(node_handle, parameters_);
        clear_current_task(&task);
        finish_result(
          goal_handle,
          false,
          ExecuteTask::Goal::STAGE_FAILED,
          ExecuteTask::Result::ERROR_EXECUTION_FAILED,
          "MTC init failed: " + message.str());
        return;
      }

      publish_feedback(
        goal_handle,
        move_home_task ?
        ExecuteTask::Goal::STAGE_MOVING_HOME :
        ExecuteTask::Goal::STAGE_MOVING_PREGRASP,
        "Planning MTC task");

      try {
        task.plan(static_cast<std::size_t>(parameters_.max_solutions));
      } catch (const mtc::InitStageException & exception) {
        std::ostringstream message;
        message << exception;
        RCLCPP_ERROR_STREAM(get_logger(), "MTC plan initialization failed:\n" << message.str());
        parameters_ = baseline_parameters;
        auto node_handle = rclcpp::Node::SharedPtr(this, [](rclcpp::Node *) {});
        factory_ = std::make_unique<TaskFactory>(node_handle, parameters_);
        clear_current_task(&task);
        finish_result(
          goal_handle,
          false,
          ExecuteTask::Goal::STAGE_FAILED,
          ExecuteTask::Result::ERROR_EXECUTION_FAILED,
          "MTC plan initialization failed: " + message.str());
        return;
      }
      if (task.solutions().empty()) {
        std::ostringstream state;
        task.printState(state);
        RCLCPP_ERROR_STREAM(get_logger(), "MTC planning state:\n" << state.str());

        std::ostringstream failure_explanation;
        task.explainFailure(failure_explanation);
        RCLCPP_ERROR_STREAM(
          get_logger(),
          "MTC planning failure explanation:\n" << failure_explanation.str());
        log_stage_solution_bounds(get_logger(), task);

        std::size_t failure_index = 0;
        for (const auto & failure : task.failures()) {
          if (!failure) {
            continue;
          }

          const auto * creator = failure->creator();
          RCLCPP_ERROR_STREAM(
            get_logger(),
            "MTC failure #" << failure_index
                            << " stage='" << (creator != nullptr ? creator->name() : "<unknown>")
                            << "' comment='" << failure->comment() << "'\n"
                            << describe_solution_state_bounds(
                              *failure,
                              "failure #" + std::to_string(failure_index)));
          ++failure_index;
        }

        parameters_ = baseline_parameters;
        auto node_handle = rclcpp::Node::SharedPtr(this, [](rclcpp::Node *) {});
        factory_ = std::make_unique<TaskFactory>(node_handle, parameters_);
        clear_current_task(&task);
        finish_result(
          goal_handle,
          false,
          ExecuteTask::Goal::STAGE_FAILED,
          ExecuteTask::Result::ERROR_PLAN_FAILED,
          "MTC planning failed. Inspect the task in RViz for the failing stage.");
        return;
      }

      auto & solutions = task.solutions();
      trajectory_processing::IterativeParabolicTimeParameterization time_parameterization;
      const std::size_t retimed_count = retime_solution_trajectories(
        *const_cast<mtc::SolutionBase *>(solutions.front().get()),
        time_parameterization,
        parameters_.cartesian_velocity_scaling,
        parameters_.cartesian_acceleration_scaling);
      if (retimed_count > 0) {
        RCLCPP_WARN(
          get_logger(),
          "Retimed %zu MTC sub-trajectories with non-increasing timestamps before execution",
          retimed_count);
      }

      task.introspection().publishSolution(*solutions.front());
      RCLCPP_INFO_STREAM(
        get_logger(),
        "MTC chosen solution tree:\n" << describe_solution_tree(*solutions.front()));
      log_solution_trajectory_timing(
        get_logger(),
        *solutions.front(),
        &task.introspection());

      if (diagnostic_ik_only) {
        parameters_ = baseline_parameters;
        auto node_handle = rclcpp::Node::SharedPtr(this, [](rclcpp::Node *) {});
        factory_ = std::make_unique<TaskFactory>(node_handle, parameters_);
        clear_current_task(&task);
        finish_result(
          goal_handle,
          true,
          ExecuteTask::Goal::STAGE_DONE,
          ExecuteTask::Result::ERROR_NONE,
          "Grasp IK probe generated at least one solution. Execution is intentionally skipped.");
        return;
      }

      if (!parameters_.execute_on_plan) {
        parameters_ = baseline_parameters;
        auto node_handle = rclcpp::Node::SharedPtr(this, [](rclcpp::Node *) {});
        factory_ = std::make_unique<TaskFactory>(node_handle, parameters_);
        clear_current_task(&task);
        finish_result(
          goal_handle,
          true,
          ExecuteTask::Goal::STAGE_DONE,
          ExecuteTask::Result::ERROR_NONE,
          "MTC plan generated successfully. Execution was disabled by parameter.");
        return;
      }

      publish_feedback(
        goal_handle,
        move_home_task ?
        ExecuteTask::Goal::STAGE_MOVING_HOME :
        ExecuteTask::Goal::STAGE_CLOSING_GRIPPER,
        pick_task ? "Executing pick MTC solution" : "Executing MTC solution");

      if (pick_task) {
        detach_pick_object_from_gazebo_link_attacher();
      }
      stop_gripper_hold();

      moveit::core::MoveItErrorCode execution_result(moveit_msgs::msg::MoveItErrorCodes::SUCCESS);
      std::string execution_error_message;
      const bool use_contact_aware_close =
        pick_task &&
        parameters_.use_contact_aware_gripper_close &&
        parameters_.gripper_close_joint7 >= 0.0;

      if (use_contact_aware_close) {
        if (!execute_solution_with_contact_aware_gripper_close(
            goal_handle,
            *solutions.front(),
            execution_error_message))
        {
          execution_result.val = moveit_msgs::msg::MoveItErrorCodes::CONTROL_FAILED;
        }
      } else {
        execution_result = task.execute(*solutions.front());
      }

      if (execution_result.val != moveit_msgs::msg::MoveItErrorCodes::SUCCESS) {
        if (pick_task) {
          detach_pick_object_from_gazebo_link_attacher();
          detach_pick_object_from_moveit();
        }
        stop_gripper_hold();
        parameters_ = baseline_parameters;
        auto node_handle = rclcpp::Node::SharedPtr(this, [](rclcpp::Node *) {});
        factory_ = std::make_unique<TaskFactory>(node_handle, parameters_);
        clear_current_task(&task);
        finish_result(
          goal_handle,
          false,
          ExecuteTask::Goal::STAGE_FAILED,
          ExecuteTask::Result::ERROR_EXECUTION_FAILED,
          execution_error_message.empty() ?
          "MTC execution failed with MoveIt error code " +
          std::to_string(execution_result.val) :
          execution_error_message);
        return;
      }

      if (pick_task && parameters_.enable_gazebo_attachment && !gazebo_link_attached()) {
        RCLCPP_WARN(
          get_logger(),
          "MTC execution succeeded, but the official Gazebo link attacher never latched '%s'",
          parameters_.pickup_object.id.c_str());
      }

      if (pick_task) {
        if (parameters_.pick_only) {
          parameters_ = baseline_parameters;
          auto node_handle = rclcpp::Node::SharedPtr(this, [](rclcpp::Node *) {});
          factory_ = std::make_unique<TaskFactory>(node_handle, parameters_);
          clear_current_task(&task);
          finish_result(
            goal_handle,
            true,
            ExecuteTask::Goal::STAGE_DONE,
            ExecuteTask::Result::ERROR_NONE,
            "Pick-only task completed.");
          return;
        }

        if (!execute_pre_place_alignment(goal_handle, execution_error_message)) {
          detach_pick_object_from_gazebo_link_attacher();
          detach_pick_object_from_moveit();
          stop_gripper_hold();
          parameters_ = baseline_parameters;
          auto node_handle = rclcpp::Node::SharedPtr(this, [](rclcpp::Node *) {});
          factory_ = std::make_unique<TaskFactory>(node_handle, parameters_);
          clear_current_task(&task);
          finish_result(
            goal_handle,
            false,
            ExecuteTask::Goal::STAGE_FAILED,
            ExecuteTask::Result::ERROR_EXECUTION_FAILED,
            execution_error_message);
          return;
        }

        if (parameters_.place_target.release_after_pre_place) {
          publish_feedback(
            goal_handle,
            ExecuteTask::Goal::STAGE_OPENING_GRIPPER,
            "Releasing object from pre-place pose");

          const bool release_success =
            execute_direct_release_fallback(goal_handle, execution_error_message);
          stop_gripper_hold();
          parameters_ = baseline_parameters;
          auto node_handle = rclcpp::Node::SharedPtr(this, [](rclcpp::Node *) {});
          factory_ = std::make_unique<TaskFactory>(node_handle, parameters_);

          if (release_success) {
            finish_result(
              goal_handle,
              true,
              ExecuteTask::Goal::STAGE_DONE,
              ExecuteTask::Result::ERROR_NONE,
              "Released object from pre-place pose.");
          } else {
            finish_result(
              goal_handle,
              false,
              ExecuteTask::Goal::STAGE_FAILED,
              ExecuteTask::Result::ERROR_EXECUTION_FAILED,
              execution_error_message.empty() ?
              "Failed to release object from pre-place pose." :
              execution_error_message);
          }
          clear_current_task(nullptr);
          return;
        }

        publish_feedback(
          goal_handle,
          ExecuteTask::Goal::STAGE_MOVING_PLACE,
          "Planning place MTC task");

        mtc::Task place_task = factory_->create_place_task();
        set_current_task(&place_task);

        try {
          place_task.init();
        } catch (const mtc::InitStageException & exception) {
          std::ostringstream message;
          message << exception;
          RCLCPP_ERROR_STREAM(get_logger(), "Place MTC init failed:\n" << message.str());
          stop_gripper_hold();
          parameters_ = baseline_parameters;
          auto node_handle = rclcpp::Node::SharedPtr(this, [](rclcpp::Node *) {});
          factory_ = std::make_unique<TaskFactory>(node_handle, parameters_);
          clear_current_task(&place_task);
          finish_result(
            goal_handle,
            false,
            ExecuteTask::Goal::STAGE_FAILED,
            ExecuteTask::Result::ERROR_EXECUTION_FAILED,
            "Place MTC init failed: " + message.str());
          return;
        }

        place_task.plan(static_cast<std::size_t>(parameters_.max_solutions));
        if (place_task.solutions().empty()) {
          std::ostringstream state;
          place_task.printState(state);
          RCLCPP_ERROR_STREAM(get_logger(), "Place MTC planning state:\n" << state.str());

          std::ostringstream failure_explanation;
          place_task.explainFailure(failure_explanation);
          RCLCPP_ERROR_STREAM(
            get_logger(),
            "Place MTC planning failure explanation:\n" << failure_explanation.str());
          log_stage_solution_bounds(get_logger(), place_task);

          if (parameters_.place_target.allow_direct_release_fallback) {
            publish_feedback(
              goal_handle,
              ExecuteTask::Goal::STAGE_OPENING_GRIPPER,
              "Place planning failed, releasing object with direct fallback");

            const bool fallback_success =
              execute_direct_release_fallback(goal_handle, execution_error_message);
            clear_current_task(&place_task);
            stop_gripper_hold();
            parameters_ = baseline_parameters;
            auto node_handle = rclcpp::Node::SharedPtr(this, [](rclcpp::Node *) {});
            factory_ = std::make_unique<TaskFactory>(node_handle, parameters_);

            if (fallback_success) {
              finish_result(
                goal_handle,
                true,
                ExecuteTask::Goal::STAGE_DONE,
                ExecuteTask::Result::ERROR_NONE,
                "Place planning failed, but direct release fallback completed.");
            } else {
              finish_result(
                goal_handle,
                false,
                ExecuteTask::Goal::STAGE_FAILED,
                ExecuteTask::Result::ERROR_EXECUTION_FAILED,
                execution_error_message.empty() ?
                "Place planning failed and direct release fallback also failed." :
                execution_error_message);
            }
            return;
          }

          stop_gripper_hold();
          parameters_ = baseline_parameters;
          auto node_handle = rclcpp::Node::SharedPtr(this, [](rclcpp::Node *) {});
          factory_ = std::make_unique<TaskFactory>(node_handle, parameters_);
          clear_current_task(&place_task);
          finish_result(
            goal_handle,
            false,
            ExecuteTask::Goal::STAGE_FAILED,
            ExecuteTask::Result::ERROR_PLAN_FAILED,
            "Place MTC planning failed. Inspect the task in RViz for the failing stage.");
          return;
        }

        auto & place_solutions = place_task.solutions();
        trajectory_processing::IterativeParabolicTimeParameterization place_time_parameterization;
        const std::size_t place_retimed_count = retime_solution_trajectories(
          *const_cast<mtc::SolutionBase *>(place_solutions.front().get()),
          place_time_parameterization,
          parameters_.cartesian_velocity_scaling,
          parameters_.cartesian_acceleration_scaling);
        if (place_retimed_count > 0) {
          RCLCPP_WARN(
            get_logger(),
            "Retimed %zu place MTC sub-trajectories with non-increasing timestamps before execution",
            place_retimed_count);
        }

        place_task.introspection().publishSolution(*place_solutions.front());
        RCLCPP_INFO_STREAM(
          get_logger(),
          "MTC chosen place solution tree:\n" << describe_solution_tree(*place_solutions.front()));
        log_solution_trajectory_timing(
          get_logger(),
          *place_solutions.front(),
          &place_task.introspection());

        publish_feedback(
          goal_handle,
          ExecuteTask::Goal::STAGE_MOVING_PLACE,
          "Executing place MTC solution");

        const auto place_execution_result =
          execute_solution_with_contact_aware_gripper_close(
          goal_handle,
          *place_solutions.front(),
          execution_error_message,
          false);
        stop_gripper_hold();
        clear_current_task(&place_task);

        if (!place_execution_result) {
          detach_pick_object_from_gazebo_link_attacher();
          detach_pick_object_from_moveit();
          parameters_ = baseline_parameters;
          auto node_handle = rclcpp::Node::SharedPtr(this, [](rclcpp::Node *) {});
          factory_ = std::make_unique<TaskFactory>(node_handle, parameters_);
          finish_result(
            goal_handle,
            false,
            ExecuteTask::Goal::STAGE_FAILED,
            ExecuteTask::Result::ERROR_EXECUTION_FAILED,
            execution_error_message.empty() ?
            "Place MTC execution failed." :
            execution_error_message);
          return;
        }
      }

      stop_gripper_hold();
      parameters_ = baseline_parameters;
      auto node_handle = rclcpp::Node::SharedPtr(this, [](rclcpp::Node *) {});
      factory_ = std::make_unique<TaskFactory>(node_handle, parameters_);
      finish_result(
        goal_handle,
        true,
        ExecuteTask::Goal::STAGE_DONE,
        ExecuteTask::Result::ERROR_NONE,
        move_home_task ?
        "Move-home MTC task completed." :
        "Pick-and-place MTC task completed.");
      clear_current_task(nullptr);
    } catch (const std::exception & exception) {
      detach_pick_object_from_gazebo_link_attacher();
      detach_pick_object_from_moveit();
      stop_gripper_hold();
      auto node_handle = rclcpp::Node::SharedPtr(this, [](rclcpp::Node *) {});
      factory_ = std::make_unique<TaskFactory>(node_handle, parameters_);
      clear_current_task(nullptr);
      finish_result(
        goal_handle,
        false,
        ExecuteTask::Goal::STAGE_FAILED,
        ExecuteTask::Result::ERROR_EXECUTION_FAILED,
        std::string("MTC task failed: ") + exception.what());
    }
  }

  void execute_observe_goal(const std::shared_ptr<GoalHandleExecuteTask> & goal_handle)
  {
    if (!parameters_.observe_pose.enabled) {
      finish_result(
        goal_handle,
        false,
        ExecuteTask::Goal::STAGE_MOVING_PREGRASP,
        ExecuteTask::Result::ERROR_NOT_READY,
        "Observe pose is not enabled in configuration.");
      clear_current_task(nullptr);
      return;
    }

    publish_feedback(
      goal_handle,
      ExecuteTask::Goal::STAGE_MOVING_PREGRASP,
      "Moving arm to observe pose");

    geometry_msgs::msg::PoseStamped observe_pose;
    observe_pose.header.frame_id = parameters_.planning_frame;
    observe_pose.pose.position.x = parameters_.observe_pose.position.x;
    observe_pose.pose.position.y = parameters_.observe_pose.position.y;
    observe_pose.pose.position.z = parameters_.observe_pose.position.z;

    tf2::Quaternion quaternion;
    quaternion.setRPY(
      parameters_.observe_pose.orientation.roll,
      parameters_.observe_pose.orientation.pitch,
      parameters_.observe_pose.orientation.yaw);
    observe_pose.pose.orientation.x = quaternion.x();
    observe_pose.pose.orientation.y = quaternion.y();
    observe_pose.pose.orientation.z = quaternion.z();
    observe_pose.pose.orientation.w = quaternion.w();

    arm_move_group_->clearPoseTargets();
    arm_move_group_->setStartStateToCurrentState();
    arm_move_group_->setPoseTarget(observe_pose, parameters_.hand_frame);

    moveit::planning_interface::MoveGroupInterface::Plan plan;
    const bool plan_success = static_cast<bool>(arm_move_group_->plan(plan));
    if (!plan_success) {
      arm_move_group_->clearPoseTargets();
      finish_result(
        goal_handle,
        false,
        ExecuteTask::Goal::STAGE_FAILED,
        ExecuteTask::Result::ERROR_PLAN_FAILED,
        "Failed to plan move to observe pose.");
      clear_current_task(nullptr);
      return;
    }

    const auto execute_result = arm_move_group_->execute(plan);
    arm_move_group_->clearPoseTargets();
    if (execute_result.val != moveit_msgs::msg::MoveItErrorCodes::SUCCESS) {
      finish_result(
        goal_handle,
        false,
        ExecuteTask::Goal::STAGE_FAILED,
        ExecuteTask::Result::ERROR_EXECUTION_FAILED,
        "Failed to execute move to observe pose.");
      clear_current_task(nullptr);
      return;
    }

    finish_result(
      goal_handle,
      true,
      ExecuteTask::Goal::STAGE_DONE,
      ExecuteTask::Result::ERROR_NONE,
      "Observe pose reached.");
    clear_current_task(nullptr);
  }

  XYZ add_xyz(const XYZ & lhs, const XYZ & rhs) const
  {
    return XYZ{lhs.x + rhs.x, lhs.y + rhs.y, lhs.z + rhs.z};
  }

  geometry_msgs::msg::PoseStamped make_pose_stamped(const XYZ & position, const RPY & orientation) const
  {
    geometry_msgs::msg::PoseStamped pose;
    pose.header.frame_id = parameters_.planning_frame;
    pose.pose.position.x = position.x;
    pose.pose.position.y = position.y;
    pose.pose.position.z = position.z;

    tf2::Quaternion quaternion;
    quaternion.setRPY(orientation.roll, orientation.pitch, orientation.yaw);
    pose.pose.orientation.x = quaternion.x();
    pose.pose.orientation.y = quaternion.y();
    pose.pose.orientation.z = quaternion.z();
    pose.pose.orientation.w = quaternion.w();
    return pose;
  }

  bool execute_arm_pose_goal(
    const std::shared_ptr<GoalHandleExecuteTask> & goal_handle,
    const geometry_msgs::msg::PoseStamped & pose,
    const std::string & stage_name,
    uint8_t feedback_stage,
    std::string & error_message)
  {
    if (goal_handle->is_canceling()) {
      error_message = "Task canceled";
      return false;
    }

    publish_feedback(goal_handle, feedback_stage, stage_name);
    RCLCPP_INFO(
      get_logger(),
      "%s pose in %s: position=(%.4f, %.4f, %.4f) orientation=(%.4f, %.4f, %.4f, %.4f)",
      stage_name.c_str(),
      pose.header.frame_id.c_str(),
      pose.pose.position.x,
      pose.pose.position.y,
      pose.pose.position.z,
      pose.pose.orientation.x,
      pose.pose.orientation.y,
      pose.pose.orientation.z,
      pose.pose.orientation.w);

    arm_move_group_->clearPoseTargets();
    arm_move_group_->setStartStateToCurrentState();
    arm_move_group_->setPoseTarget(pose, parameters_.hand_frame);

    moveit::planning_interface::MoveGroupInterface::Plan plan;
    const bool plan_success = static_cast<bool>(arm_move_group_->plan(plan));
    if (!plan_success) {
      arm_move_group_->clearPoseTargets();
      error_message = "Failed to plan pose goal for stage '" + stage_name + "'.";
      return false;
    }

    const auto execute_result = arm_move_group_->execute(plan);
    arm_move_group_->clearPoseTargets();
    if (execute_result.val != moveit_msgs::msg::MoveItErrorCodes::SUCCESS) {
      error_message =
        "Failed to execute pose goal for stage '" + stage_name + "' (MoveIt error code " +
        std::to_string(execute_result.val) + ").";
      return false;
    }
    return true;
  }

  bool validate_classification_place_config(std::string & error_message) const
  {
    const auto & config = parameters_.classification_place;
    if (!config.enabled) {
      error_message = "Classification place task is not enabled in configuration.";
      return false;
    }
    if (config.platform_slots.empty()) {
      error_message = "classification_place.platform_slots_xyz is empty.";
      return false;
    }
    if (config.platform_slots.size() != config.platform_slot_classes.size() ||
      config.platform_slots.size() != config.box_classes.size())
    {
      error_message =
        "classification_place platform_slots, platform_slot_classes, and box_classes must have the same length.";
      return false;
    }
    return true;
  }

  bool set_fusion_target_class(const std::string & target_class, std::string & error_message)
  {
    const auto & config = parameters_.classification_place;
    if (!config.set_fusion_target_class) {
      return true;
    }
    if (!target_fusion_parameter_client_) {
      error_message = "Target fusion parameter client is unavailable.";
      return false;
    }
    if (!target_fusion_parameter_client_->wait_for_service(std::chrono::seconds(2))) {
      error_message =
        "Timed out waiting for parameter service on " + config.target_fusion_node_name + ".";
      return false;
    }

    auto future = target_fusion_parameter_client_->set_parameters(
      {rclcpp::Parameter("target_class", target_class)});
    if (future.wait_for(std::chrono::seconds(2)) != std::future_status::ready) {
      error_message = "Timed out setting grasp_target_fusion target_class to '" + target_class + "'.";
      return false;
    }
    const auto results = future.get();
    for (const auto & result : results) {
      if (!result.successful) {
        error_message =
          "Failed to set grasp_target_fusion target_class to '" + target_class +
          "': " + result.reason;
        return false;
      }
    }

    const double settle_sec = std::max(0.0, config.target_switch_settle_sec);
    if (settle_sec > 1e-6) {
      std::this_thread::sleep_for(std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::duration<double>(settle_sec)));
    }
    return true;
  }

  bool wait_for_box_target(
    const std::string & box_class,
    const rclcpp::Time & not_before,
    GraspTarget & target,
    std::string & error_message)
  {
    const auto & config = parameters_.classification_place;
    const auto deadline = now() + rclcpp::Duration::from_seconds(
      std::max(0.0, config.box_target_timeout_sec));
    const std::string normalized_box_class = normalize_class_name(box_class);

    while (rclcpp::ok()) {
      {
        std::lock_guard<std::mutex> lock(vision_target_mutex_);
        if (!latest_grasp_target_) {
          error_message = "No box target has been received yet.";
        } else if ((latest_grasp_target_received_at_ - not_before).seconds() < 0.0) {
          error_message = "Waiting for a fresh box target.";
        } else if (latest_grasp_target_->header.frame_id != parameters_.planning_frame) {
          error_message = "Latest box target is not expressed in the planning frame.";
        } else if (normalize_class_name(latest_grasp_target_->class_name) != normalized_box_class) {
          error_message =
            "Latest box target class is '" + latest_grasp_target_->class_name +
            "', waiting for '" + box_class + "'.";
        } else if (latest_grasp_target_->confidence < config.min_box_confidence) {
          error_message = "Latest box target confidence is below threshold.";
        } else if (parameters_.vision_target.require_valid_signal && !latest_target_valid_) {
          error_message = "Latest box target is currently marked invalid.";
        } else {
          target = *latest_grasp_target_;
          return true;
        }
      }

      if (now() >= deadline) {
        break;
      }
      std::this_thread::sleep_for(std::chrono::milliseconds(50));
    }

    if (error_message.empty()) {
      error_message = "Timed out waiting for box target '" + box_class + "'.";
    }
    return false;
  }

  bool execute_classification_pick_from_slot(
    const std::shared_ptr<GoalHandleExecuteTask> & goal_handle,
    std::size_t slot_index,
    std::string & error_message)
  {
    const auto & config = parameters_.classification_place;
    const auto slot = config.platform_slots[slot_index];
    const auto block_class = config.platform_slot_classes[slot_index];

    stop_gripper_hold();
    detach_pick_object_from_gazebo_link_attacher();
    detach_pick_object_from_moveit();

    publish_feedback(
      goal_handle,
      ExecuteTask::Goal::STAGE_OPENING_GRIPPER,
      "Opening gripper for " + block_class);
    if (parameters_.gripper_open_joint7 >= -0.5) {
      publish_gripper_target(parameters_.gripper_open_joint7, 0.40);
    } else if (!execute_named_gripper_target(
        parameters_.gripper_open_named_target,
        "opening for classification pick",
        error_message))
    {
      return false;
    }
    std::this_thread::sleep_for(std::chrono::milliseconds(500));

    if (!execute_arm_pose_goal(
        goal_handle,
        make_pose_stamped(add_xyz(slot, config.pregrasp_offset), config.grasp_orientation),
        "Moving to " + block_class + " platform pregrasp",
        ExecuteTask::Goal::STAGE_MOVING_PREGRASP,
        error_message))
    {
      return false;
    }

    if (!execute_arm_pose_goal(
        goal_handle,
        make_pose_stamped(slot, config.grasp_orientation),
        "Moving to " + block_class + " platform grasp",
        ExecuteTask::Goal::STAGE_MOVING_GRASP,
        error_message))
    {
      return false;
    }

    publish_feedback(
      goal_handle,
      ExecuteTask::Goal::STAGE_CLOSING_GRIPPER,
      "Closing gripper on " + block_class);
    if (parameters_.gripper_close_joint7 >= -0.5) {
      publish_gripper_target(parameters_.gripper_close_joint7, 0.50);
    } else if (!execute_named_gripper_target(
        parameters_.gripper_close_named_target,
        "closing for classification pick",
        error_message))
    {
      return false;
    }
    std::this_thread::sleep_for(std::chrono::milliseconds(800));

    if (!execute_arm_pose_goal(
        goal_handle,
        make_pose_stamped(add_xyz(slot, config.lift_offset), config.grasp_orientation),
        "Lifting " + block_class + " from platform",
        ExecuteTask::Goal::STAGE_LIFTING,
        error_message))
    {
      return false;
    }

    return true;
  }

  bool execute_classification_release_to_box(
    const std::shared_ptr<GoalHandleExecuteTask> & goal_handle,
    const GraspTarget & box_target,
    std::string & error_message)
  {
    const auto & config = parameters_.classification_place;
    XYZ release_position{
      box_target.pose.position.x + config.release_offset.x,
      box_target.pose.position.y + config.release_offset.y,
      box_target.pose.position.z + config.release_offset.z};

    if (!execute_arm_pose_goal(
        goal_handle,
        make_pose_stamped(release_position, config.grasp_orientation),
        "Moving above " + box_target.class_name + " for release",
        ExecuteTask::Goal::STAGE_MOVING_PLACE,
        error_message))
    {
      return false;
    }

    publish_feedback(
      goal_handle,
      ExecuteTask::Goal::STAGE_OPENING_GRIPPER,
      "Releasing block into " + box_target.class_name);
    return execute_direct_release_fallback(goal_handle, error_message);
  }

  void execute_classification_place_goal(const std::shared_ptr<GoalHandleExecuteTask> & goal_handle)
  {
    std::string error_message;
    if (!validate_classification_place_config(error_message)) {
      finish_result(
        goal_handle,
        false,
        ExecuteTask::Goal::STAGE_FAILED,
        ExecuteTask::Result::ERROR_NOT_READY,
        error_message);
      clear_current_task(nullptr);
      return;
    }

    try {
      stop_gripper_hold();
      if (parameters_.observe_pose.enabled) {
        if (!execute_arm_pose_goal(
            goal_handle,
            make_pose_stamped(parameters_.observe_pose.position, parameters_.observe_pose.orientation),
            "Moving to classification observe pose",
            ExecuteTask::Goal::STAGE_MOVING_PREGRASP,
            error_message))
        {
          finish_result(
            goal_handle,
            false,
            ExecuteTask::Goal::STAGE_FAILED,
            ExecuteTask::Result::ERROR_EXECUTION_FAILED,
            error_message);
          clear_current_task(nullptr);
          return;
        }
      }

      const auto & config = parameters_.classification_place;
      std::vector<GraspTarget> box_targets(config.box_classes.size());
      for (std::size_t box_index = 0; box_index < config.box_classes.size(); ++box_index) {
        const auto & box_class = config.box_classes[box_index];
        publish_feedback(
          goal_handle,
          ExecuteTask::Goal::STAGE_WAITING_FOR_TARGET,
          "Locating " + box_class + " target");

        const auto target_switch_started_at = now();
        if (!set_fusion_target_class(box_class, error_message)) {
          finish_result(
            goal_handle,
            false,
            ExecuteTask::Goal::STAGE_WAITING_FOR_TARGET,
            ExecuteTask::Result::ERROR_NOT_READY,
            error_message);
          clear_current_task(nullptr);
          return;
        }

        if (!wait_for_box_target(box_class, target_switch_started_at, box_targets[box_index], error_message)) {
          finish_result(
            goal_handle,
            false,
            ExecuteTask::Goal::STAGE_WAITING_FOR_TARGET,
            ExecuteTask::Result::ERROR_TIMEOUT,
            error_message);
          clear_current_task(nullptr);
          return;
        }
      }

      for (std::size_t slot_index = 0; slot_index < config.platform_slots.size(); ++slot_index) {
        if (goal_handle->is_canceling()) {
          finish_result(
            goal_handle,
            false,
            ExecuteTask::Goal::STAGE_FAILED,
            ExecuteTask::Result::ERROR_CANCELED,
            "Classification place task canceled.");
          clear_current_task(nullptr);
          return;
        }

        const auto & block_class = config.platform_slot_classes[slot_index];
        const auto & box_class = config.box_classes[slot_index];
        RCLCPP_INFO(
          get_logger(),
          "Classification step %zu/%zu: pick '%s' from platform slot, place into '%s'",
          slot_index + 1,
          config.platform_slots.size(),
          block_class.c_str(),
          box_class.c_str());

        if (!execute_classification_pick_from_slot(goal_handle, slot_index, error_message)) {
          finish_result(
            goal_handle,
            false,
            ExecuteTask::Goal::STAGE_FAILED,
            ExecuteTask::Result::ERROR_EXECUTION_FAILED,
            error_message);
          clear_current_task(nullptr);
          return;
        }

        if (!execute_classification_release_to_box(goal_handle, box_targets[slot_index], error_message)) {
          finish_result(
            goal_handle,
            false,
            ExecuteTask::Goal::STAGE_FAILED,
            ExecuteTask::Result::ERROR_EXECUTION_FAILED,
            error_message);
          clear_current_task(nullptr);
          return;
        }
      }

      finish_result(
        goal_handle,
        true,
        ExecuteTask::Goal::STAGE_DONE,
        ExecuteTask::Result::ERROR_NONE,
        "Classification place task completed.");
      clear_current_task(nullptr);
    } catch (const std::exception & exception) {
      stop_gripper_hold();
      detach_pick_object_from_gazebo_link_attacher();
      detach_pick_object_from_moveit();
      finish_result(
        goal_handle,
        false,
        ExecuteTask::Goal::STAGE_FAILED,
        ExecuteTask::Result::ERROR_EXECUTION_FAILED,
        std::string("Classification place task failed: ") + exception.what());
      clear_current_task(nullptr);
    }
  }

  bool execute_pre_place_alignment(
    const std::shared_ptr<GoalHandleExecuteTask> & goal_handle,
    std::string & error_message)
  {
    if (!parameters_.pre_place.enabled) {
      return true;
    }

    const auto initial_pose = arm_move_group_->getCurrentPose(parameters_.hand_frame);

    if (parameters_.pre_place.coarse_base_first) {
      const auto current_joint_values = arm_move_group_->getCurrentJointValues();
      const auto joint_names = arm_move_group_->getJointNames();
      const auto joint_it = std::find(
        joint_names.begin(),
        joint_names.end(),
        parameters_.pre_place.base_joint_name);
      if (joint_it == joint_names.end()) {
        error_message =
          "Pre-place base joint '" + parameters_.pre_place.base_joint_name + "' not found.";
        return false;
      }
      const std::size_t joint_index =
        static_cast<std::size_t>(std::distance(joint_names.begin(), joint_it));
      if (joint_index >= current_joint_values.size()) {
        error_message =
          "Pre-place base joint index is out of range for current joint state.";
        return false;
      }

      auto current_state = arm_move_group_->getCurrentState(5.0);
      if (!current_state) {
        error_message = "Failed to read current robot state for coarse pre-place alignment.";
        return false;
      }

      const double current_base_angle = current_joint_values[joint_index];
      const double current_object_angle =
        std::atan2(initial_pose.pose.position.y, initial_pose.pose.position.x);
      const double current_object_radius =
        std::hypot(initial_pose.pose.position.x, initial_pose.pose.position.y);
      const double desired_object_angle =
        choose_good_enough_object_angle(
        current_object_angle,
        current_object_radius,
        parameters_.place_bin,
        parameters_.pickup_object.radius) + parameters_.pre_place.heading_offset;
      const double desired_base_angle =
        current_base_angle + normalize_angle(desired_object_angle - current_object_angle);
      const auto & bounds =
        current_state->getRobotModel()->getVariableBounds(parameters_.pre_place.base_joint_name);
      const double target_base_angle = choose_nearest_bounded_angle(
        current_base_angle,
        desired_base_angle,
        bounds);

      if (std::abs(target_base_angle - current_base_angle) >= parameters_.pre_place.min_delta) {
        std::vector<double> coarse_joint_values = current_joint_values;
        coarse_joint_values[joint_index] = target_base_angle;

        publish_feedback(
          goal_handle,
          ExecuteTask::Goal::STAGE_MOVING_PLACE,
          "Coarsely rotating base toward place bin");

        arm_move_group_->clearPoseTargets();
        arm_move_group_->setStartStateToCurrentState();
        arm_move_group_->setJointValueTarget(coarse_joint_values);

        moveit::planning_interface::MoveGroupInterface::Plan coarse_plan;
        const bool coarse_success = static_cast<bool>(arm_move_group_->plan(coarse_plan));
        if (!coarse_success) {
          error_message = "Failed to plan coarse base rotation toward place bin.";
          return false;
        }

        const auto coarse_execute_result = arm_move_group_->execute(coarse_plan);
        if (coarse_execute_result.val != moveit_msgs::msg::MoveItErrorCodes::SUCCESS) {
          error_message = "Failed to execute coarse base rotation toward place bin.";
          return false;
        }
      }
    }

    if (std::abs(parameters_.pre_place.retract_joint3_delta) >= 1e-6 ||
      std::abs(parameters_.pre_place.retract_joint4_delta) >= 1e-6)
    {
      auto retract_joint_values = arm_move_group_->getCurrentJointValues();
      const auto joint_names = arm_move_group_->getJointNames();

      const auto joint3_it = std::find(
        joint_names.begin(),
        joint_names.end(),
        parameters_.pre_place.retract_joint3_name);
      const auto joint4_it = std::find(
        joint_names.begin(),
        joint_names.end(),
        parameters_.pre_place.retract_joint4_name);

      if (joint3_it != joint_names.end() &&
        static_cast<std::size_t>(std::distance(joint_names.begin(), joint3_it)) <
        retract_joint_values.size())
      {
        const std::size_t joint3_index =
          static_cast<std::size_t>(std::distance(joint_names.begin(), joint3_it));
        retract_joint_values[joint3_index] += parameters_.pre_place.retract_joint3_delta;
      }

      if (joint4_it != joint_names.end() &&
        static_cast<std::size_t>(std::distance(joint_names.begin(), joint4_it)) <
        retract_joint_values.size())
      {
        const std::size_t joint4_index =
          static_cast<std::size_t>(std::distance(joint_names.begin(), joint4_it));
        retract_joint_values[joint4_index] += parameters_.pre_place.retract_joint4_delta;
      }

      publish_feedback(
        goal_handle,
        ExecuteTask::Goal::STAGE_MOVING_PLACE,
        "Retracting elbow and wrist toward release pose");

      arm_move_group_->clearPoseTargets();
      arm_move_group_->setStartStateToCurrentState();
      arm_move_group_->setJointValueTarget(retract_joint_values);

      moveit::planning_interface::MoveGroupInterface::Plan retract_plan;
      const bool retract_success = static_cast<bool>(arm_move_group_->plan(retract_plan));
      if (!retract_success) {
        RCLCPP_WARN(
          get_logger(),
          "Failed to plan elbow/wrist retract step. Continuing without it.");
      } else {
        const auto retract_execute_result = arm_move_group_->execute(retract_plan);
        if (retract_execute_result.val != moveit_msgs::msg::MoveItErrorCodes::SUCCESS) {
          RCLCPP_WARN(
            get_logger(),
            "Failed to execute elbow/wrist retract step (MoveIt error code %d). Continuing without it.",
            retract_execute_result.val);
        }
      }
    }

    if (!parameters_.pre_place.hover_after_base) {
      return true;
    }

    const auto current_pose = arm_move_group_->getCurrentPose(parameters_.hand_frame);
    geometry_msgs::msg::PoseStamped target_pose = current_pose;
    target_pose.header.frame_id = parameters_.planning_frame;

    const double bin_top_z =
      parameters_.place_bin.center.z + 0.5 * parameters_.place_bin.size.z;
    const double safe_hover_z = std::max(
      current_pose.pose.position.z,
      bin_top_z + parameters_.pickup_object.height + parameters_.pre_place.hover_margin_z);

    const double current_xy_angle = std::atan2(
      current_pose.pose.position.y,
      current_pose.pose.position.x);
    const double current_radius = std::hypot(
      current_pose.pose.position.x,
      current_pose.pose.position.y);
    const double desired_hover_radius = std::max(
      0.0,
      std::hypot(parameters_.place_bin.center.x, parameters_.place_bin.center.y) +
      parameters_.pre_place.hover_margin_xy);
    const double target_radius = std::min(current_radius, desired_hover_radius);
    target_pose.pose.position.x = target_radius * std::cos(current_xy_angle);
    target_pose.pose.position.y = target_radius * std::sin(current_xy_angle);
    target_pose.pose.position.z = safe_hover_z;

    tf2::Quaternion target_orientation;
    target_orientation.setRPY(
      parameters_.place_target.orientation.roll,
      parameters_.place_target.orientation.pitch,
      parameters_.place_target.orientation.yaw);
    target_pose.pose.orientation.x = target_orientation.x();
    target_pose.pose.orientation.y = target_orientation.y();
    target_pose.pose.orientation.z = target_orientation.z();
    target_pose.pose.orientation.w = target_orientation.w();

    const double dx = target_pose.pose.position.x - current_pose.pose.position.x;
    const double dy = target_pose.pose.position.y - current_pose.pose.position.y;
    const double dz = target_pose.pose.position.z - current_pose.pose.position.z;

    tf2::Quaternion current_orientation(
      current_pose.pose.orientation.x,
      current_pose.pose.orientation.y,
      current_pose.pose.orientation.z,
      current_pose.pose.orientation.w);
    const double orientation_alignment =
      std::clamp(std::abs(current_orientation.dot(target_orientation)), 0.0, 1.0);
    const double orientation_delta = 2.0 * std::acos(orientation_alignment);

    if (std::sqrt(dx * dx + dy * dy + dz * dz) < parameters_.pre_place.min_delta &&
      orientation_delta < 0.05)
    {
      return true;
    }

    publish_feedback(
      goal_handle,
      ExecuteTask::Goal::STAGE_MOVING_PLACE,
      "Moving above place bin center");

    arm_move_group_->clearPoseTargets();
    arm_move_group_->setStartStateToCurrentState();
    arm_move_group_->setPoseTarget(target_pose, parameters_.hand_frame);

    moveit::planning_interface::MoveGroupInterface::Plan plan;
    const bool plan_success = static_cast<bool>(arm_move_group_->plan(plan));
    if (!plan_success) {
      arm_move_group_->clearPoseTargets();
      RCLCPP_WARN(
        get_logger(),
        "Failed to plan move above place bin center. Continuing with coarse pre-place alignment only.");
      error_message.clear();
      return true;
    }

    const auto execute_result = arm_move_group_->execute(plan);
    arm_move_group_->clearPoseTargets();
    if (execute_result.val != moveit_msgs::msg::MoveItErrorCodes::SUCCESS) {
      RCLCPP_WARN(
        get_logger(),
        "Failed to execute move above place bin center (MoveIt error code %d). "
        "Continuing with coarse pre-place alignment only.",
        execute_result.val);
      error_message.clear();
      return true;
    }

    return true;
  }

  bool execute_direct_release_fallback(
    const std::shared_ptr<GoalHandleExecuteTask> & goal_handle,
    std::string & error_message)
  {
    if (goal_handle->is_canceling()) {
      error_message = "Task canceled";
      return false;
    }

    stop_gripper_hold();

    if (parameters_.gripper_open_joint7 >= -0.5) {
      publish_gripper_target(parameters_.gripper_open_joint7, 0.35);
      std::this_thread::sleep_for(std::chrono::milliseconds(500));
    } else {
      if (!execute_named_gripper_target(
          parameters_.gripper_open_named_target,
          "opening for direct release fallback",
          error_message))
      {
        return false;
      }
    }

    detach_pick_object_from_gazebo_link_attacher();
    detach_pick_object_from_moveit();

    const double retreat_distance = std::max(0.0, parameters_.place_target.direct_release_retreat_z);
    if (retreat_distance <= 1e-6) {
      return true;
    }

    auto current_state = arm_move_group_->getCurrentState(5.0);
    if (!current_state) {
      RCLCPP_WARN(
        get_logger(),
        "Object released, but failed to query current arm state for retreat. "
        "Treating retreat as best-effort complete.");
      error_message.clear();
      return true;
    }

    const auto current_pose = arm_move_group_->getCurrentPose(parameters_.hand_frame);
    geometry_msgs::msg::Pose retreat_pose = current_pose.pose;
    retreat_pose.position.z += retreat_distance;

    moveit_msgs::msg::RobotTrajectory trajectory_message;
    moveit_msgs::msg::MoveItErrorCodes moveit_error_code;
    const double achieved_fraction = arm_move_group_->computeCartesianPath(
      std::vector<geometry_msgs::msg::Pose>{retreat_pose},
      std::max(parameters_.cartesian_step_size, 0.001),
      parameters_.cartesian_jump_threshold,
      trajectory_message,
      false,
      &moveit_error_code);
    if (achieved_fraction < 0.99) {
      RCLCPP_WARN(
        get_logger(),
        "Object released, but direct-release retreat Cartesian path only achieved fraction %.3f. "
        "Keeping the release result and skipping further retreat.",
        achieved_fraction);
      error_message.clear();
      return true;
    }

    robot_trajectory::RobotTrajectory retreat_trajectory(
      arm_move_group_->getRobotModel(),
      parameters_.arm_group_name);
    retreat_trajectory.setRobotTrajectoryMsg(*current_state, trajectory_message);

    trajectory_processing::IterativeParabolicTimeParameterization time_parameterization;
    if (!time_parameterization.computeTimeStamps(
        retreat_trajectory,
        parameters_.cartesian_velocity_scaling,
        parameters_.cartesian_acceleration_scaling))
    {
      RCLCPP_WARN(
        get_logger(),
        "Object released, but failed to time-parameterize direct-release retreat. "
        "Keeping the release result.");
      error_message.clear();
      return true;
    }

    retreat_trajectory.getRobotTrajectoryMsg(trajectory_message);
    publish_feedback(
      goal_handle,
      ExecuteTask::Goal::STAGE_MOVING_PLACE,
      "Retreating upward after direct release");

    const auto retreat_execute_result = arm_move_group_->execute(trajectory_message);
    if (retreat_execute_result.val != moveit_msgs::msg::MoveItErrorCodes::SUCCESS) {
      RCLCPP_WARN(
        get_logger(),
        "Object released, but upward retreat failed with MoveIt error code %d. "
        "Keeping the release result.",
        retreat_execute_result.val);
      error_message.clear();
      return true;
    }

    return true;
  }

  bool get_selected_fixed_place_position(XYZ & position, std::string & error_message)
  {
    const auto candidates =
      get_parameter("place_target.fixed_pose_candidates_xyz").as_double_array();
    if (candidates.empty() || candidates.size() % 3 != 0) {
      error_message =
        "Parameter 'place_target.fixed_pose_candidates_xyz' must contain one or more xyz triples.";
      return false;
    }

    const int64_t index = get_parameter("place_target.fixed_pose_index").as_int();
    const int64_t candidate_count = static_cast<int64_t>(candidates.size() / 3);
    if (index < 0 || index >= candidate_count) {
      error_message =
        "Parameter 'place_target.fixed_pose_index' is out of range. Valid range is [0, " +
        std::to_string(candidate_count - 1) + "].";
      return false;
    }

    const std::size_t offset = static_cast<std::size_t>(index) * 3;
    position.x = candidates[offset];
    position.y = candidates[offset + 1];
    position.z = candidates[offset + 2];
    RCLCPP_INFO(
      get_logger(),
      "Selected fixed place pose index %ld: position=(%.4f, %.4f, %.4f)",
      index,
      position.x,
      position.y,
      position.z);
    return true;
  }

  bool execute_direct_visual_pick(
    const std::shared_ptr<GoalHandleExecuteTask> & goal_handle,
    std::string & error_message)
  {
    const auto make_pose_for_offset =
      [&](const TaskParameters & candidate_parameters, const XYZ & target_offset) {
        TaskParameters local_parameters = candidate_parameters;
        local_parameters.grasp_target_offset = target_offset;

      Eigen::Isometry3d object_transform = Eigen::Isometry3d::Identity();
      object_transform.translation().x() = parameters_.pickup_object.center.x;
      object_transform.translation().y() = parameters_.pickup_object.center.y;
      object_transform.translation().z() = parameters_.pickup_object.center.z;

      const Eigen::Isometry3d grasp_frame_in_hand =
        make_grasp_frame_transform(local_parameters);
      const Eigen::Isometry3d hand_transform =
        object_transform * grasp_frame_in_hand.inverse();

      geometry_msgs::msg::PoseStamped pose;
      pose.header.frame_id = candidate_parameters.planning_frame;
      pose.pose.position.x = hand_transform.translation().x();
      pose.pose.position.y = hand_transform.translation().y();
      pose.pose.position.z = hand_transform.translation().z();
      const Eigen::Quaterniond hand_orientation(hand_transform.rotation());
      pose.pose.orientation.x = hand_orientation.x();
      pose.pose.orientation.y = hand_orientation.y();
      pose.pose.orientation.z = hand_orientation.z();
      pose.pose.orientation.w = hand_orientation.w();
      return pose;
    };

    const auto execute_pose_goal =
      [&](
        const geometry_msgs::msg::PoseStamped & pose,
        const std::string & stage_name,
        uint8_t feedback_stage) {
        publish_feedback(
          goal_handle,
          feedback_stage,
          stage_name);

        RCLCPP_INFO(
          get_logger(),
          "%s pose in %s: position=(%.4f, %.4f, %.4f) orientation=(%.4f, %.4f, %.4f, %.4f)",
          stage_name.c_str(),
          pose.header.frame_id.c_str(),
          pose.pose.position.x,
          pose.pose.position.y,
          pose.pose.position.z,
          pose.pose.orientation.x,
          pose.pose.orientation.y,
          pose.pose.orientation.z,
          pose.pose.orientation.w);

        arm_move_group_->clearPoseTargets();
        arm_move_group_->setStartStateToCurrentState();
        arm_move_group_->setPoseTarget(pose, parameters_.hand_frame);

        moveit::planning_interface::MoveGroupInterface::Plan plan;
        const bool plan_success = static_cast<bool>(arm_move_group_->plan(plan));
        if (!plan_success) {
          arm_move_group_->clearPoseTargets();
          error_message = "Failed to plan pose goal for stage '" + stage_name + "'.";
          return false;
        }

        const auto execute_result = arm_move_group_->execute(plan);
        arm_move_group_->clearPoseTargets();
        if (execute_result.val != moveit_msgs::msg::MoveItErrorCodes::SUCCESS) {
          error_message =
            "Failed to execute pose goal for stage '" + stage_name + "' (MoveIt error code " +
            std::to_string(execute_result.val) + ").";
          return false;
        }
        return true;
      };

    std::vector<TaskParameters> direct_candidates;
    const auto add_direct_candidate = [&](double yaw) {
      const double normalized_yaw = normalize_angle(yaw);
      const auto existing = std::find_if(
        direct_candidates.begin(),
        direct_candidates.end(),
        [normalized_yaw](const TaskParameters & candidate) {
          return std::abs(
            normalize_angle(candidate.grasp_orientation.yaw - normalized_yaw)) < 1e-6;
        });
      if (existing != direct_candidates.end()) {
        return;
      }

      TaskParameters candidate = parameters_;
      candidate.grasp_orientation.yaw = normalized_yaw;
      direct_candidates.push_back(candidate);
    };

    add_direct_candidate(parameters_.grasp_orientation.yaw);
    for (const double yaw : parameters_.top_down_yaw_candidates) {
      add_direct_candidate(yaw);
    }
    if (direct_candidates.empty()) {
      direct_candidates.push_back(parameters_);
    }

    detach_pick_object_from_gazebo_link_attacher();
    detach_pick_object_from_moveit();
    stop_gripper_hold();

    if (!parameters_.skip_open_gripper_stage) {
      publish_feedback(
        goal_handle,
        ExecuteTask::Goal::STAGE_OPENING_GRIPPER,
        "Opening gripper");
      if (parameters_.gripper_open_joint7 >= -0.5) {
        publish_gripper_target(parameters_.gripper_open_joint7, 0.40);
      } else {
        if (!execute_named_gripper_target(
            parameters_.gripper_open_named_target,
            "opening",
            error_message))
        {
          return false;
        }
      }
      std::this_thread::sleep_for(std::chrono::milliseconds(600));
    }

    bool reached_grasp = false;
    for (std::size_t candidate_index = 0; candidate_index < direct_candidates.size();
      ++candidate_index)
    {
      const auto & candidate = direct_candidates[candidate_index];
      std::ostringstream candidate_label;
      candidate_label << "candidate " << (candidate_index + 1) << "/" << direct_candidates.size()
                      << " rpy=(" << std::fixed << std::setprecision(4)
                      << candidate.grasp_orientation.roll << ", "
                      << candidate.grasp_orientation.pitch << ", "
                      << candidate.grasp_orientation.yaw << ")";
      RCLCPP_INFO(
        get_logger(),
        "Trying direct visual pick %s",
        candidate_label.str().c_str());

      if (candidate.approach_max_distance > 1e-6 || candidate.approach_min_distance > 1e-6) {
        if (!execute_pose_goal(
            make_pose_for_offset(candidate, candidate.pregrasp_offset),
            "Moving to pregrasp " + candidate_label.str(),
            ExecuteTask::Goal::STAGE_MOVING_PREGRASP))
        {
          RCLCPP_WARN(
            get_logger(),
            "Pregrasp planning failed for direct visual pick %s, trying direct grasp.",
            candidate_label.str().c_str());
        }
      }

      if (execute_pose_goal(
          make_pose_for_offset(candidate, candidate.grasp_target_offset),
          "Moving to grasp " + candidate_label.str(),
          ExecuteTask::Goal::STAGE_MOVING_GRASP))
      {
        reached_grasp = true;
        break;
      }

      RCLCPP_WARN(
        get_logger(),
        "Direct visual pick %s failed before gripper close.",
        candidate_label.str().c_str());
    }

    if (!reached_grasp) {
      if (error_message.empty()) {
        error_message = "Failed to plan pose goal for all direct visual pick candidates.";
      }
      return false;
    }

    publish_feedback(
      goal_handle,
      ExecuteTask::Goal::STAGE_CLOSING_GRIPPER,
      "Closing gripper");
    if (parameters_.gripper_close_joint7 >= -0.5) {
      publish_gripper_target(parameters_.gripper_close_joint7, 0.50);
    } else {
      if (!execute_named_gripper_target(
          parameters_.gripper_close_named_target,
          "closing",
          error_message))
      {
        return false;
      }
    }
    std::this_thread::sleep_for(std::chrono::milliseconds(800));

    if (!attach_pick_object_to_moveit(error_message)) {
      return false;
    }
    if (parameters_.enable_gazebo_attachment &&
      !attach_pick_object_with_gazebo_link_attacher(error_message))
    {
      return false;
    }

    if (has_cartesian_distance(parameters_.lift_min_distance, parameters_.lift_max_distance)) {
      publish_feedback(
        goal_handle,
        ExecuteTask::Goal::STAGE_LIFTING,
        "Lifting object");
      if (!execute_explicit_lift(goal_handle, error_message)) {
        return false;
      }
    }

    const auto current_pose_after_lift = arm_move_group_->getCurrentPose(parameters_.hand_frame);
    XYZ fixed_place_position;
    if (!get_selected_fixed_place_position(fixed_place_position, error_message)) {
      return false;
    }

    geometry_msgs::msg::PoseStamped fixed_place_pose;
    fixed_place_pose.header.frame_id = parameters_.planning_frame;
    fixed_place_pose.pose.position.x = fixed_place_position.x;
    fixed_place_pose.pose.position.y = fixed_place_position.y;
    fixed_place_pose.pose.position.z = fixed_place_position.z;
    fixed_place_pose.pose.orientation = current_pose_after_lift.pose.orientation;

    if (!execute_pose_goal(
        fixed_place_pose,
        "Moving to fixed place pose",
        ExecuteTask::Goal::STAGE_MOVING_PLACE))
    {
      return false;
    }

    publish_feedback(
      goal_handle,
      ExecuteTask::Goal::STAGE_OPENING_GRIPPER,
      "Releasing object at fixed place pose");
    if (!execute_direct_release_fallback(goal_handle, error_message)) {
      return false;
    }
    return true;
  }

  void set_current_task(mtc::Task * task)
  {
    std::lock_guard<std::mutex> lock(current_task_mutex_);
    current_task_ = task;
  }

  void clear_current_task(mtc::Task * task)
  {
    std::lock_guard<std::mutex> lock(current_task_mutex_);
    if (task == nullptr || current_task_ == task) {
      current_task_ = nullptr;
      active_goal_ = false;
    }
  }

  void run_autostart_task()
  {
    autostart_timer_->cancel();
    RCLCPP_INFO(
      get_logger(),
      "autostart_task_type=%ld is configured. Send an action goal to '%s' to execute it.",
      parameters_.autostart_task_type,
      parameters_.action_name.c_str());
  }

  void handle_joint_state(const sensor_msgs::msg::JointState::SharedPtr message)
  {
    for (std::size_t index = 0; index < message->name.size() && index < message->position.size(); ++index) {
      if (message->name[index] != "joint7") {
        continue;
      }

      std::lock_guard<std::mutex> lock(gazebo_attachment_mutex_);
      latest_joint7_position_ = message->position[index];
      have_joint7_position_ = true;
      return;
    }
  }

  void handle_grasp_target(const GraspTarget::SharedPtr message)
  {
    std::lock_guard<std::mutex> lock(vision_target_mutex_);
    latest_grasp_target_ = *message;
    latest_grasp_target_received_at_ = now();
  }

  void handle_target_valid(const std_msgs::msg::Bool::SharedPtr message)
  {
    std::lock_guard<std::mutex> lock(vision_target_mutex_);
    latest_target_valid_ = message->data;
  }

  bool wait_for_visual_target_after(
    const rclcpp::Time & not_before,
    double timeout_sec,
    std::string & error_message)
  {
    const double bounded_timeout_sec = std::max(0.0, timeout_sec);
    const auto deadline = now() + rclcpp::Duration::from_seconds(bounded_timeout_sec);
    std::string latest_usable_error_message;

    while (rclcpp::ok()) {
      {
        std::lock_guard<std::mutex> lock(vision_target_mutex_);
        if (latest_grasp_target_) {
          if (is_visual_target_usable_locked(&latest_usable_error_message)) {
            if ((latest_grasp_target_received_at_ - not_before).seconds() >= 0.0) {
              return true;
            }
          } else {
            error_message = latest_usable_error_message;
          }
        } else {
          error_message = "No visual target has been received yet.";
        }
      }

      if (now() >= deadline) {
        break;
      }
      std::this_thread::sleep_for(std::chrono::milliseconds(50));
    }

    {
      std::lock_guard<std::mutex> lock(vision_target_mutex_);
      if (latest_grasp_target_ && is_visual_target_usable_locked(&latest_usable_error_message)) {
        RCLCPP_WARN(
          get_logger(),
          "No post-home visual target arrived within %.2f s; using the latest still-valid target.",
          bounded_timeout_sec);
        return true;
      }
    }

    if (error_message.empty()) {
      if (!latest_usable_error_message.empty()) {
        error_message = latest_usable_error_message;
      } else {
        error_message = "Timed out waiting for a usable visual target after moving home.";
      }
    }
    return false;
  }

  bool wait_for_fresh_visual_target_after(
    const rclcpp::Time & not_before,
    double timeout_sec,
    std::string & error_message)
  {
    const double bounded_timeout_sec = std::max(0.0, timeout_sec);
    const auto deadline = now() + rclcpp::Duration::from_seconds(bounded_timeout_sec);

    while (rclcpp::ok()) {
      {
        std::lock_guard<std::mutex> lock(vision_target_mutex_);
        if (latest_grasp_target_ &&
          (latest_grasp_target_received_at_ - not_before).seconds() >= 0.0)
        {
          if (is_visual_target_usable_locked(&error_message)) {
            return true;
          }
        } else {
          error_message = "No fresh visual target has been received after moving home.";
        }
      }

      if (now() >= deadline) {
        break;
      }
      std::this_thread::sleep_for(std::chrono::milliseconds(50));
    }

    if (error_message.empty()) {
      error_message = "Timed out waiting for a fresh visual target after moving home.";
    }
    return false;
  }

  bool prepare_visual_pick_target(std::string & error_message)
  {
    std::lock_guard<std::mutex> lock(vision_target_mutex_);
    if (!parameters_.vision_target.enabled) {
      error_message = "Visual target mode is not enabled in configuration.";
      return false;
    }

    if (!is_visual_target_usable_locked(&error_message)) {
      return false;
    }

    parameters_.pickup_object.center.x =
      latest_grasp_target_->pose.position.x + parameters_.vision_target.target_position_bias.x;
    parameters_.pickup_object.center.y =
      latest_grasp_target_->pose.position.y + parameters_.vision_target.target_position_bias.y;
    parameters_.pickup_object.center.z =
      latest_grasp_target_->pose.position.z + parameters_.vision_target.target_position_bias.z;
    const double size_x = latest_grasp_target_->size.x > 1e-6 ?
      latest_grasp_target_->size.x : parameters_.vision_target.default_target_size.x;
    const double size_y = latest_grasp_target_->size.y > 1e-6 ?
      latest_grasp_target_->size.y : parameters_.vision_target.default_target_size.y;
    const double size_z = latest_grasp_target_->size.z > 1e-6 ?
      latest_grasp_target_->size.z : parameters_.vision_target.default_target_size.z;
    const double collision_scale_xy = positive_or(parameters_.vision_target.collision_scale_xy, 1.0);
    const double collision_scale_z = positive_or(parameters_.vision_target.collision_scale_z, 1.0);
    parameters_.pickup_object.radius = 0.5 * std::max(size_x, size_y) * collision_scale_xy;
    parameters_.pickup_object.height = size_z * collision_scale_z;

    if (latest_grasp_target_->has_yaw) {
      std::vector<double> yaw_candidates;
      yaw_candidates.reserve(parameters_.vision_target.yaw_candidate_offsets.size());
      for (const double offset : parameters_.vision_target.yaw_candidate_offsets) {
        yaw_candidates.push_back(normalize_angle(latest_grasp_target_->yaw + offset));
      }
      if (yaw_candidates.empty()) {
        yaw_candidates.push_back(normalize_angle(latest_grasp_target_->yaw));
      }
      parameters_.top_down_yaw_candidates = yaw_candidates;
    }

    const auto grasp_strategy =
      normalize_class_name(parameters_.vision_target.grasp_strategy);
    if (parameters_.vision_target.compute_grasp_offsets && grasp_strategy == "radial_side") {
      const double center_norm_xy = std::hypot(
        parameters_.pickup_object.center.x,
        parameters_.pickup_object.center.y);
      XYZ approach_direction{1.0, 0.0, 0.0};
      if (center_norm_xy > 1e-6) {
        approach_direction.x = parameters_.pickup_object.center.x / center_norm_xy;
        approach_direction.y = parameters_.pickup_object.center.y / center_norm_xy;
        approach_direction.z = 0.0;
      }
      if (parameters_.vision_target.lock_lateral_offsets_to_zero) {
        approach_direction.x = approach_direction.x >= 0.0 ? 1.0 : -1.0;
        approach_direction.y = 0.0;
        approach_direction.z = 0.0;
      }
      const double radial_yaw =
        normalize_angle(std::atan2(approach_direction.y, approach_direction.x));
      parameters_.grasp_orientation.yaw = radial_yaw;

      const double clearance = std::max(0.0, parameters_.vision_target.grasp_clearance);
      const double pregrasp_distance =
        std::max(0.0, parameters_.vision_target.pregrasp_distance);
      const double grasp_radius = parameters_.pickup_object.radius + clearance;
      const double grasp_z =
        0.5 * parameters_.pickup_object.height + parameters_.vision_target.grasp_z_offset;

      parameters_.approach_direction = approach_direction;
      parameters_.grasp_target_offset = {
        -approach_direction.x * grasp_radius,
        -approach_direction.y * grasp_radius,
        grasp_z};
      parameters_.pregrasp_offset = {
        parameters_.grasp_target_offset.x - approach_direction.x * pregrasp_distance,
        parameters_.grasp_target_offset.y - approach_direction.y * pregrasp_distance,
        grasp_z};

      parameters_.top_down_grasp_target_x_candidates =
        make_single_candidate(parameters_.grasp_target_offset.x);
      parameters_.top_down_grasp_target_y_candidates =
        make_single_candidate(parameters_.grasp_target_offset.y);
      parameters_.top_down_grasp_target_z_candidates =
        make_single_candidate(parameters_.grasp_target_offset.z);
      parameters_.top_down_pregrasp_x_candidates =
        make_single_candidate(parameters_.pregrasp_offset.x);
      parameters_.top_down_pregrasp_y_candidates =
        make_single_candidate(parameters_.pregrasp_offset.y);
      parameters_.top_down_pregrasp_z_candidates =
        make_single_candidate(parameters_.pregrasp_offset.z);
      parameters_.top_down_approach_direction_candidates = {
        approach_direction.x,
        approach_direction.y,
        approach_direction.z};
      parameters_.top_down_roll_candidates =
        make_single_candidate(parameters_.grasp_orientation.roll);
      parameters_.top_down_pitch_candidates =
        make_single_candidate(parameters_.grasp_orientation.pitch);
      parameters_.top_down_yaw_candidates.clear();
      append_unique_angle_candidate(parameters_.top_down_yaw_candidates, radial_yaw);
      for (const double offset : parameters_.vision_target.yaw_candidate_offsets) {
        append_unique_angle_candidate(parameters_.top_down_yaw_candidates, radial_yaw + offset);
      }

      if (!has_cartesian_distance(parameters_.approach_min_distance, parameters_.approach_max_distance) &&
        pregrasp_distance > 1e-6)
      {
        parameters_.approach_min_distance = 0.75 * pregrasp_distance;
        parameters_.approach_max_distance = pregrasp_distance;
      }

      RCLCPP_INFO(
        get_logger(),
        "Visual grasp geometry: raw_target=(%.4f, %.4f, %.4f) "
        "bias=(%.4f, %.4f, %.4f) target=(%.4f, %.4f, %.4f) size=(%.4f, %.4f, %.4f) "
        "collision_radius=%.4f collision_height=%.4f grasp_offset=(%.4f, %.4f, %.4f) "
        "pregrasp_offset=(%.4f, %.4f, %.4f) approach=(%.4f, %.4f, %.4f) "
        "orientation_rpy=(%.4f, %.4f, %.4f) approach_distance=[%.4f, %.4f]",
        latest_grasp_target_->pose.position.x,
        latest_grasp_target_->pose.position.y,
        latest_grasp_target_->pose.position.z,
        parameters_.vision_target.target_position_bias.x,
        parameters_.vision_target.target_position_bias.y,
        parameters_.vision_target.target_position_bias.z,
        parameters_.pickup_object.center.x,
        parameters_.pickup_object.center.y,
        parameters_.pickup_object.center.z,
        size_x,
        size_y,
        size_z,
        parameters_.pickup_object.radius,
        parameters_.pickup_object.height,
        parameters_.grasp_target_offset.x,
        parameters_.grasp_target_offset.y,
        parameters_.grasp_target_offset.z,
        parameters_.pregrasp_offset.x,
        parameters_.pregrasp_offset.y,
        parameters_.pregrasp_offset.z,
        parameters_.approach_direction.x,
        parameters_.approach_direction.y,
        parameters_.approach_direction.z,
        parameters_.grasp_orientation.roll,
        parameters_.grasp_orientation.pitch,
        parameters_.grasp_orientation.yaw,
        parameters_.approach_min_distance,
        parameters_.approach_max_distance);
    }

    auto node_handle = rclcpp::Node::SharedPtr(this, [](rclcpp::Node *) {});
    factory_ = std::make_unique<TaskFactory>(node_handle, parameters_);
    return true;
  }

  bool is_visual_target_usable_locked(std::string * error_message) const
  {
    if (!latest_grasp_target_) {
      if (error_message != nullptr) {
        *error_message = "No visual target has been received yet.";
      }
      return false;
    }

    if (parameters_.vision_target.require_valid_signal && !latest_target_valid_) {
      if (error_message != nullptr) {
        *error_message = "Latest visual target is currently marked invalid.";
      }
      return false;
    }

    const auto age = (now() - latest_grasp_target_received_at_).seconds();
    if (age > parameters_.vision_target.target_timeout_sec) {
      if (error_message != nullptr) {
        *error_message = "Latest visual target is stale.";
      }
      return false;
    }

    if (latest_grasp_target_->header.frame_id != parameters_.planning_frame) {
      if (error_message != nullptr) {
        *error_message = "Latest visual target is not expressed in the planning frame.";
      }
      return false;
    }

    if (latest_grasp_target_->confidence < parameters_.vision_target.min_target_confidence) {
      if (error_message != nullptr) {
        *error_message = "Latest visual target confidence is below threshold.";
      }
      return false;
    }

    const std::string normalized = normalize_class_name(latest_grasp_target_->class_name);
    const auto allowed = std::find_if(
      parameters_.vision_target.allowed_target_classes.begin(),
      parameters_.vision_target.allowed_target_classes.end(),
      [&normalized](const std::string & candidate) {
        return normalize_class_name(candidate) == normalized;
      });
    if (allowed == parameters_.vision_target.allowed_target_classes.end()) {
      if (error_message != nullptr) {
        *error_message = "Latest visual target class is not allowed.";
      }
      return false;
    }

    return true;
  }

  bool execute_solution_with_contact_aware_gripper_close(
    const std::shared_ptr<GoalHandleExecuteTask> & goal_handle,
    const mtc::SolutionBase & solution,
    std::string & error_message,
    bool close_gripper_on_contact = true)
  {
    std::vector<ExecutableTrajectoryStep> steps;
    collect_executable_trajectory_steps(solution, steps);
    if (steps.empty()) {
      error_message = "MTC solution did not contain executable trajectories.";
      return false;
    }

    bool has_lift_step = false;
    std::ostringstream step_list;
    step_list << "Executable MTC trajectory steps:";
    for (const auto & step : steps) {
      step_list << "\n  stage='" << step.stage_name
                << "' joints=" << step.trajectory.joint_trajectory.joint_names.size()
                << " points=" << step.trajectory.joint_trajectory.points.size();
      if (stage_name_contains(step.stage_name, "lift")) {
        has_lift_step = true;
      }
    }
    RCLCPP_INFO_STREAM(get_logger(), step_list.str());
    if (!has_lift_step) {
      RCLCPP_WARN(get_logger(), "No explicit 'lift' step was found in the executable MTC sub-trajectories");
    }

    for (const auto & step : steps) {
      if (goal_handle->is_canceling()) {
        error_message = "Task canceled";
        return false;
      }

      publish_feedback(
        goal_handle,
        feedback_stage_for_step(step.stage_name),
        "Executing stage '" + step.stage_name + "'");

      if (stage_name_contains(step.stage_name, "open gripper")) {
        stop_gripper_hold();
        detach_pick_object_from_gazebo_link_attacher();
        detach_pick_object_from_moveit();
      }

      if (close_gripper_on_contact && stage_name_contains(step.stage_name, "close gripper")) {
        if (!execute_contact_aware_gripper_close(goal_handle, error_message)) {
          return false;
        }
        if (!attach_pick_object_to_moveit(error_message)) {
          return false;
        }
        if (parameters_.enable_gazebo_attachment &&
          !attach_pick_object_with_gazebo_link_attacher(error_message))
        {
          return false;
        }
        continue;
      }

      if (close_gripper_on_contact && stage_name_contains(step.stage_name, "lift")) {
        if (!execute_explicit_lift(goal_handle, error_message)) {
          return false;
        }
        continue;
      }

      const auto & trajectory = step.trajectory;
      const auto execution_result =
        trajectory_targets_gripper(trajectory) ?
        gripper_move_group_->execute(trajectory) :
        arm_move_group_->execute(trajectory);
      if (execution_result.val != moveit_msgs::msg::MoveItErrorCodes::SUCCESS) {
        error_message =
          "Failed to execute stage '" + step.stage_name + "' with MoveIt error code " +
          std::to_string(execution_result.val);
        return false;
      }
    }

    return true;
  }

  bool execute_explicit_lift(
    const std::shared_ptr<GoalHandleExecuteTask> & goal_handle,
    std::string & error_message)
  {
    if (goal_handle->is_canceling()) {
      error_message = "Task canceled";
      return false;
    }

    const double direction_norm = std::sqrt(
      parameters_.lift_direction.x * parameters_.lift_direction.x +
      parameters_.lift_direction.y * parameters_.lift_direction.y +
      parameters_.lift_direction.z * parameters_.lift_direction.z);
    if (direction_norm <= 1e-9) {
      error_message = "Lift direction is zero-length.";
      return false;
    }

    const double lift_distance =
      std::max(parameters_.lift_min_distance, parameters_.lift_max_distance);
    if (lift_distance <= 1e-6) {
      return true;
    }

    auto current_state = arm_move_group_->getCurrentState(5.0);
    if (!current_state) {
      error_message = "Failed to query current arm state before explicit lift.";
      return false;
    }

    const auto current_pose = arm_move_group_->getCurrentPose(parameters_.hand_frame);
    geometry_msgs::msg::Pose target_pose = current_pose.pose;
    target_pose.position.x += (parameters_.lift_direction.x / direction_norm) * lift_distance;
    target_pose.position.y += (parameters_.lift_direction.y / direction_norm) * lift_distance;
    target_pose.position.z += (parameters_.lift_direction.z / direction_norm) * lift_distance;

    moveit_msgs::msg::RobotTrajectory trajectory_message;
    moveit_msgs::msg::MoveItErrorCodes error_code;
    const double achieved_fraction = arm_move_group_->computeCartesianPath(
      std::vector<geometry_msgs::msg::Pose>{target_pose},
      std::max(parameters_.cartesian_step_size, 0.001),
      parameters_.cartesian_jump_threshold,
      trajectory_message,
      false,
      &error_code);
    const double achieved_lift_distance = achieved_fraction * lift_distance;
    if (achieved_fraction < 0.99) {
      const double required_lift_distance =
        std::max(parameters_.lift_min_distance, 0.0);
      if (achieved_lift_distance + 1e-6 < required_lift_distance) {
        error_message =
          "Explicit lift Cartesian path only achieved fraction " +
          std::to_string(achieved_fraction) +
          " (distance " + std::to_string(achieved_lift_distance) +
          " m, required at least " + std::to_string(required_lift_distance) + " m)";
        return false;
      }

      RCLCPP_WARN(
        get_logger(),
        "Explicit lift Cartesian path only achieved fraction %.6f, but that still yields %.4f m "
        "which meets the required minimum %.4f m. Executing the partial lift.",
        achieved_fraction,
        achieved_lift_distance,
        required_lift_distance);
    }

    robot_trajectory::RobotTrajectory lift_trajectory(
      arm_move_group_->getRobotModel(),
      parameters_.arm_group_name);
    lift_trajectory.setRobotTrajectoryMsg(*current_state, trajectory_message);

    trajectory_processing::IterativeParabolicTimeParameterization time_parameterization;
    if (!time_parameterization.computeTimeStamps(
        lift_trajectory,
        parameters_.cartesian_velocity_scaling,
        parameters_.cartesian_acceleration_scaling))
    {
      error_message = "Failed to time-parameterize explicit lift trajectory.";
      return false;
    }

    lift_trajectory.getRobotTrajectoryMsg(trajectory_message);

    const auto execution_result = arm_move_group_->execute(trajectory_message);
    if (execution_result.val != moveit_msgs::msg::MoveItErrorCodes::SUCCESS) {
      error_message =
        "Explicit lift execution failed with MoveIt error code " +
        std::to_string(execution_result.val);
      return false;
    }

    return true;
  }

  bool execute_contact_aware_gripper_close(
    const std::shared_ptr<GoalHandleExecuteTask> & goal_handle,
    std::string & error_message)
  {
    constexpr double kCloseStepJoint7 = 0.0040;
    constexpr double kContactPreloadJoint7 = 0.0015;
    constexpr double kReachTolerance = 0.0006;
    constexpr double kProgressEpsilon = 0.0002;
    constexpr double kCommandDurationSec = 0.40;
    constexpr double kStepTimeoutSec = 1.2;
    constexpr double kStallTimeoutSec = 0.60;
    constexpr double kPollIntervalSec = 0.02;

    if (!wait_for_joint7_state(kStepTimeoutSec, error_message)) {
      return false;
    }

    const double final_target = std::clamp(parameters_.gripper_close_joint7, 0.0, 0.035);
    double current_position = latest_joint7_position();

    while (current_position - final_target > kReachTolerance) {
      if (goal_handle->is_canceling()) {
        error_message = "Task canceled";
        return false;
      }

      const double commanded_target = std::max(final_target, current_position - kCloseStepJoint7);
      publish_gripper_target(commanded_target, kCommandDurationSec);

      const auto step_started_at = std::chrono::steady_clock::now();
      auto last_progress_time = step_started_at;
      double last_progress_position = current_position;
      bool reached_command = false;
      bool stalled = false;

      while (std::chrono::duration<double>(std::chrono::steady_clock::now() - step_started_at).count() <
        kStepTimeoutSec)
      {
        std::this_thread::sleep_for(
          std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::duration<double>(kPollIntervalSec)));

        const double observed_position = latest_joint7_position();
        if (observed_position <= commanded_target + kReachTolerance) {
          current_position = observed_position;
          reached_command = true;
          break;
        }

        if (last_progress_position - observed_position > kProgressEpsilon) {
          last_progress_position = observed_position;
          last_progress_time = std::chrono::steady_clock::now();
        } else if (
          std::chrono::duration<double>(std::chrono::steady_clock::now() - last_progress_time).count() >=
          kStallTimeoutSec)
        {
          current_position = observed_position;
          stalled = true;
          break;
        }
      }

      if (reached_command) {
        continue;
      }

      if (stalled) {
        const double hold_target =
          std::max(final_target, current_position - kContactPreloadJoint7);
        start_gripper_hold(hold_target);
        if (!wait_for_gripper_hold_engaged(hold_target, 0.5, error_message)) {
          return false;
        }
        RCLCPP_INFO(
          get_logger(),
          "Stopped gripper close after contact-like stall: target=%.4f, contact=%.4f, hold=%.4f",
          commanded_target,
          current_position,
          hold_target);
        return true;
      }

      error_message =
        "Gripper close step timed out before reaching its target or detecting a stable contact.";
      return false;
    }

    start_gripper_hold(final_target);
    if (!wait_for_gripper_hold_engaged(final_target, 0.5, error_message)) {
      return false;
    }
    return true;
  }

  bool wait_for_joint7_state(double timeout_sec, std::string & error_message)
  {
    const auto started_at = std::chrono::steady_clock::now();
    while (std::chrono::duration<double>(std::chrono::steady_clock::now() - started_at).count() <
      timeout_sec)
    {
      {
        std::lock_guard<std::mutex> lock(gazebo_attachment_mutex_);
        if (have_joint7_position_) {
          return true;
        }
      }
      std::this_thread::sleep_for(std::chrono::milliseconds(20));
    }

    error_message = "Timed out waiting for joint7 state feedback.";
    return false;
  }

  double latest_joint7_position()
  {
    std::lock_guard<std::mutex> lock(gazebo_attachment_mutex_);
    return latest_joint7_position_;
  }

  double normalize_direct_gripper_target(double joint7_target)
  {
    // MoveIt gripper semantics in this workspace are: open is negative, close is zero.
    // Preserve compatibility with older positive-open configs by mirroring them here.
    if (joint7_target > 0.0) {
      return -std::clamp(joint7_target, 0.0, 0.035);
    }
    return std::clamp(joint7_target, -0.040, 0.0);
  }

  bool execute_named_gripper_target(
    const std::string & named_target,
    const std::string & action_label,
    std::string & error_message)
  {
    gripper_move_group_->setStartStateToCurrentState();
    if (!gripper_move_group_->setNamedTarget(named_target)) {
      error_message = "Failed to set gripper " + action_label + " target.";
      return false;
    }

    moveit::planning_interface::MoveGroupInterface::Plan gripper_plan;
    if (!static_cast<bool>(gripper_move_group_->plan(gripper_plan))) {
      error_message = "Failed to plan gripper " + action_label + ".";
      return false;
    }

    const auto gripper_execute_result = gripper_move_group_->execute(gripper_plan);
    if (gripper_execute_result.val != moveit_msgs::msg::MoveItErrorCodes::SUCCESS) {
      error_message = "Failed to execute gripper " + action_label + ".";
      return false;
    }
    return true;
  }

  bool execute_named_arm_target(
    const std::string & named_target,
    const std::string & action_label,
    std::string & error_message)
  {
    arm_move_group_->clearPoseTargets();
    arm_move_group_->setStartStateToCurrentState();
    if (!arm_move_group_->setNamedTarget(named_target)) {
      error_message = "Failed to set arm " + action_label + " target '" + named_target + "'.";
      arm_move_group_->clearPoseTargets();
      return false;
    }

    moveit::planning_interface::MoveGroupInterface::Plan arm_plan;
    if (!static_cast<bool>(arm_move_group_->plan(arm_plan))) {
      error_message = "Failed to plan arm " + action_label + " target '" + named_target + "'.";
      arm_move_group_->clearPoseTargets();
      return false;
    }

    const auto arm_execute_result = arm_move_group_->execute(arm_plan);
    arm_move_group_->clearPoseTargets();
    if (arm_execute_result.val != moveit_msgs::msg::MoveItErrorCodes::SUCCESS) {
      error_message =
        "Failed to execute arm " + action_label + " target '" + named_target +
        "' with MoveIt error code " + std::to_string(arm_execute_result.val) + ".";
      return false;
    }
    return true;
  }

  void publish_gripper_target(double joint7_target, double duration_sec)
  {
    moveit::planning_interface::MoveGroupInterface::Plan plan;
    auto & joint_trajectory = plan.trajectory_.joint_trajectory;
    joint_trajectory.joint_names = {"joint7"};

    auto start_point = trajectory_msgs::msg::JointTrajectoryPoint();
    start_point.positions = {std::clamp(latest_joint7_position(), -0.040, 0.0)};
    start_point.time_from_start = rclcpp::Duration::from_seconds(0.0);
    joint_trajectory.points.push_back(std::move(start_point));

    auto target_point = trajectory_msgs::msg::JointTrajectoryPoint();
    target_point.positions = {normalize_direct_gripper_target(joint7_target)};
    target_point.time_from_start = rclcpp::Duration::from_seconds(duration_sec);
    joint_trajectory.points.push_back(std::move(target_point));

    const auto execute_result = gripper_move_group_->execute(plan);
    if (execute_result.val != moveit_msgs::msg::MoveItErrorCodes::SUCCESS) {
      RCLCPP_WARN(
        get_logger(),
        "Failed to execute gripper target through MoveIt bridge, error code %d",
        execute_result.val);
    }
  }

  void start_gripper_hold(double joint7_target)
  {
    {
      std::lock_guard<std::mutex> lock(gripper_hold_mutex_);
      gripper_hold_target_ = std::clamp(joint7_target, 0.0, 0.035);
      gripper_hold_active_ = true;
    }
    publish_active_gripper_hold();
  }

  void stop_gripper_hold()
  {
    {
      std::lock_guard<std::mutex> lock(gripper_hold_mutex_);
      gripper_hold_active_ = false;
    }
  }

  bool gripper_hold_active()
  {
    std::lock_guard<std::mutex> lock(gripper_hold_mutex_);
    return gripper_hold_active_;
  }

  bool wait_for_gripper_hold_engaged(
    double hold_target,
    double timeout_sec,
    std::string & error_message)
  {
    const auto started_at = std::chrono::steady_clock::now();
    double last_position = latest_joint7_position();

    while (std::chrono::duration<double>(std::chrono::steady_clock::now() - started_at).count() <
      timeout_sec)
    {
      std::this_thread::sleep_for(std::chrono::milliseconds(20));
      const double observed_position = latest_joint7_position();

      if (observed_position <= hold_target + 0.0008) {
        return true;
      }

      // If the gripper is still making inward progress, keep waiting for it to settle.
      if (observed_position < last_position - 0.0001) {
        last_position = observed_position;
        continue;
      }
    }

    const double observed_position = latest_joint7_position();
    RCLCPP_WARN(
      get_logger(),
      "Gripper hold did not settle onto target before lift: hold_target=%.4f observed=%.4f. "
      "Continuing with best-effort hold.",
      hold_target,
      observed_position);
    error_message.clear();
    return true;
  }

  void publish_active_gripper_hold()
  {
    double hold_target = 0.0;
    {
      std::lock_guard<std::mutex> lock(gripper_hold_mutex_);
      if (!gripper_hold_active_) {
        return;
      }
      hold_target = gripper_hold_target_;
    }
    publish_gripper_target(hold_target, 0.40);
  }

  bool attach_pick_object_to_moveit(std::string & error_message)
  {
    const bool attached =
      parameters_.touch_links.empty() ?
      arm_move_group_->attachObject(parameters_.pickup_object.id, parameters_.hand_frame) :
      arm_move_group_->attachObject(
      parameters_.pickup_object.id,
      parameters_.hand_frame,
      parameters_.touch_links);
    if (!attached) {
      error_message =
        "Gripper contact succeeded, but failed to attach the object into MoveIt's planning scene.";
      return false;
    }

    RCLCPP_INFO(
      get_logger(),
      "Attached '%s' to '%s' for manual pick execution",
      parameters_.pickup_object.id.c_str(),
      parameters_.hand_frame.c_str());
    return true;
  }

  void detach_pick_object_from_moveit()
  {
    arm_move_group_->detachObject(parameters_.pickup_object.id);
  }

  bool attach_pick_object_with_gazebo_link_attacher(std::string & error_message)
  {
#if !defined(HAVE_LINKATTACHER_MSGS)
    (void)error_message;
    return true;
#else
    if (!parameters_.enable_gazebo_attachment) {
      return true;
    }

    if (!gazebo_attach_link_client_) {
      error_message = "Official Gazebo link attacher client is unavailable.";
      return false;
    }
    if (!gazebo_attach_link_client_->wait_for_service(std::chrono::seconds(2))) {
      error_message = "Timed out waiting for the /ATTACHLINK service.";
      return false;
    }

    auto request = std::make_shared<AttachLink::Request>();
    request->model1_name = parameters_.gazebo_attach_robot_model;
    request->link1_name = parameters_.gazebo_attach_robot_link;
    request->model2_name = parameters_.gazebo_attach_object_model;
    request->link2_name = parameters_.gazebo_attach_object_link;

    auto future = gazebo_attach_link_client_->async_send_request(request);
    if (future.wait_for(std::chrono::seconds(2)) != std::future_status::ready) {
      error_message = "Timed out waiting for the /ATTACHLINK response.";
      return false;
    }

    const auto response = future.get();
    if (!response->success) {
      error_message = "Gazebo link attacher failed: " + response->message;
      return false;
    }

    {
      std::lock_guard<std::mutex> lock(gazebo_attachment_mutex_);
      gazebo_block_attached_ = true;
    }

    RCLCPP_INFO(
      get_logger(),
      "Official Gazebo link attacher latched '%s/%s' to '%s/%s'",
      request->model2_name.c_str(),
      request->link2_name.c_str(),
      request->model1_name.c_str(),
      request->link1_name.c_str());
    return true;
#endif
  }

  void detach_pick_object_from_gazebo_link_attacher()
  {
#if !defined(HAVE_LINKATTACHER_MSGS)
    return;
#else
    if (!parameters_.enable_gazebo_attachment || !gazebo_detach_link_client_) {
      return;
    }

    bool attached = false;
    {
      std::lock_guard<std::mutex> lock(gazebo_attachment_mutex_);
      attached = gazebo_block_attached_;
    }
    if (!attached) {
      return;
    }

    if (!gazebo_detach_link_client_->wait_for_service(std::chrono::milliseconds(500))) {
      RCLCPP_WARN(
        get_logger(),
        "Skipping Gazebo detach because /DETACHLINK is unavailable");
      return;
    }

    auto request = std::make_shared<DetachLink::Request>();
    request->model1_name = parameters_.gazebo_attach_robot_model;
    request->link1_name = parameters_.gazebo_attach_robot_link;
    request->model2_name = parameters_.gazebo_attach_object_model;
    request->link2_name = parameters_.gazebo_attach_object_link;

    auto future = gazebo_detach_link_client_->async_send_request(request);
    if (future.wait_for(std::chrono::seconds(2)) != std::future_status::ready) {
      RCLCPP_WARN(get_logger(), "Timed out waiting for /DETACHLINK");
      return;
    }

    const auto response = future.get();
    if (!response->success) {
      RCLCPP_WARN(
        get_logger(),
        "Gazebo link detacher reported failure: %s",
        response->message.c_str());
      return;
    }

    {
      std::lock_guard<std::mutex> lock(gazebo_attachment_mutex_);
      gazebo_block_attached_ = false;
    }

    RCLCPP_INFO(
      get_logger(),
      "Official Gazebo link attacher detached '%s/%s' from '%s/%s'",
      request->model2_name.c_str(),
      request->link2_name.c_str(),
      request->model1_name.c_str(),
      request->link1_name.c_str());
#endif
  }

  bool gazebo_link_attached()
  {
#if !defined(HAVE_LINKATTACHER_MSGS)
    return false;
#else
    std::lock_guard<std::mutex> lock(gazebo_attachment_mutex_);
    return gazebo_block_attached_;
#endif
  }

  TaskParameters parameters_;
  std::unique_ptr<TaskFactory> factory_;
  std::unique_ptr<SceneManager> scene_manager_;
  std::unique_ptr<moveit::planning_interface::MoveGroupInterface> arm_move_group_;
  std::unique_ptr<moveit::planning_interface::MoveGroupInterface> gripper_move_group_;
  std::shared_ptr<rclcpp::AsyncParametersClient> target_fusion_parameter_client_;
  rclcpp::CallbackGroup::SharedPtr action_callback_group_;
  rclcpp::CallbackGroup::SharedPtr gazebo_callback_group_;
  rclcpp_action::Server<ExecuteTask>::SharedPtr action_server_;
#if defined(HAVE_LINKATTACHER_MSGS)
  rclcpp::Client<AttachLink>::SharedPtr gazebo_attach_link_client_;
  rclcpp::Client<DetachLink>::SharedPtr gazebo_detach_link_client_;
#endif
  rclcpp::Subscription<sensor_msgs::msg::JointState>::SharedPtr joint_state_subscription_;
  rclcpp::Subscription<GraspTarget>::SharedPtr grasp_target_subscription_;
  rclcpp::Subscription<std_msgs::msg::Bool>::SharedPtr target_valid_subscription_;
  rclcpp::TimerBase::SharedPtr autostart_timer_;
  std::mutex current_task_mutex_;
  std::mutex gazebo_attachment_mutex_;
  std::mutex gripper_hold_mutex_;
  std::mutex vision_target_mutex_;
  mtc::Task * current_task_{nullptr};
  bool active_goal_{false};
  bool gazebo_block_attached_{false};
  bool have_joint7_position_{false};
  bool gripper_hold_active_{false};
  double gripper_hold_target_{0.0};
  double latest_joint7_position_{0.0};
  bool latest_target_valid_{false};
  std::optional<GraspTarget> latest_grasp_target_;
  rclcpp::Time latest_grasp_target_received_at_{0, 0, RCL_ROS_TIME};
};

}  // namespace piper_mtc_tasks

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  auto node = std::make_shared<piper_mtc_tasks::PickPlaceServer>();
  rclcpp::executors::MultiThreadedExecutor executor;
  executor.add_node(node);
  executor.spin();
  rclcpp::shutdown();
  return 0;
}
