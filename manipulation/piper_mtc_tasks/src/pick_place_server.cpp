#include <algorithm>
#include <chrono>
#include <cmath>
#include <future>
#include <iomanip>
#include <memory>
#include <mutex>
#include <sstream>
#include <string>
#include <thread>
#include <vector>

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
#include <linkattacher_msgs/srv/attach_link.hpp>
#include <linkattacher_msgs/srv/detach_link.hpp>
#include <rclcpp/rclcpp.hpp>
#include <rclcpp_action/rclcpp_action.hpp>
#include <sensor_msgs/msg/joint_state.hpp>
#include <trajectory_msgs/msg/joint_trajectory.hpp>
#include <trajectory_msgs/msg/joint_trajectory_point.hpp>

#include <venom_manipulation_interfaces/action/execute_task.hpp>

#include "piper_mtc_tasks/scene_manager.hpp"
#include "piper_mtc_tasks/task_factory.hpp"

namespace piper_mtc_tasks
{

namespace
{

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
  using AttachLink = linkattacher_msgs::srv::AttachLink;
  using DetachLink = linkattacher_msgs::srv::DetachLink;
  using GoalHandleExecuteTask = rclcpp_action::ServerGoalHandle<ExecuteTask>;

  PickPlaceServer()
  : Node("pick_place_server")
  {
    declare_task_parameters(*this);
    parameters_ = load_task_parameters(*this);
    auto node_handle = rclcpp::Node::SharedPtr(this, [](rclcpp::Node *) {});
    factory_ = std::make_unique<TaskFactory>(node_handle, parameters_);
    scene_manager_ = std::make_unique<SceneManager>(get_logger());
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

    gripper_command_publisher_ =
      create_publisher<trajectory_msgs::msg::JointTrajectory>(
      "/gripper_controller/joint_trajectory",
      10);

    if (parameters_.enable_gazebo_attachment) {
      gazebo_attach_link_client_ = create_client<AttachLink>(
        "/ATTACHLINK",
        rmw_qos_profile_services_default,
        gazebo_callback_group_);
      gazebo_detach_link_client_ = create_client<DetachLink>(
        "/DETACHLINK",
        rmw_qos_profile_services_default,
        gazebo_callback_group_);
    }

    rclcpp::SubscriptionOptions joint_state_options;
    joint_state_options.callback_group = gazebo_callback_group_;
    joint_state_subscription_ = create_subscription<sensor_msgs::msg::JointState>(
      "/joint_states",
      rclcpp::SensorDataQoS(),
      std::bind(&PickPlaceServer::handle_joint_state, this, std::placeholders::_1),
      joint_state_options);

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
      goal->task_type != ExecuteTask::Goal::MOVE_HOME)
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
    const bool pick_task = task_type == ExecuteTask::Goal::PICK_AND_PLACE_FIXED;
    const bool diagnostic_ik_only = pick_task && parameters_.diagnostic_ik_only;

    try {
      publish_feedback(
        goal_handle,
        task_type == ExecuteTask::Goal::MOVE_HOME ?
        ExecuteTask::Goal::STAGE_MOVING_HOME :
        ExecuteTask::Goal::STAGE_MOVING_PREGRASP,
        "Building MTC task");

      mtc::Task task =
        task_type == ExecuteTask::Goal::MOVE_HOME ?
        factory_->create_move_home_task() :
        diagnostic_ik_only ?
        factory_->create_grasp_ik_probe_task() :
        factory_->create_pick_task();
      set_current_task(&task);

      if (pick_task) {
        detach_pick_object_from_moveit();
      }

      if (pick_task && !scene_manager_->sync_pick_scene(parameters_))
      {
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
        task_type == ExecuteTask::Goal::MOVE_HOME ?
        ExecuteTask::Goal::STAGE_MOVING_HOME :
        ExecuteTask::Goal::STAGE_MOVING_PREGRASP,
        "Planning MTC task");

      task.plan(static_cast<std::size_t>(parameters_.max_solutions));
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
        task_type == ExecuteTask::Goal::MOVE_HOME ?
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
          parameters_.pickup_block.id.c_str());
      }

      if (pick_task) {
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

          stop_gripper_hold();
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
      finish_result(
        goal_handle,
        true,
        ExecuteTask::Goal::STAGE_DONE,
        ExecuteTask::Result::ERROR_NONE,
        task_type == ExecuteTask::Goal::MOVE_HOME ?
        "Move-home MTC task completed." :
        "Pick-and-place MTC task completed.");
      clear_current_task(nullptr);
    } catch (const std::exception & exception) {
      detach_pick_object_from_gazebo_link_attacher();
      detach_pick_object_from_moveit();
      stop_gripper_hold();
      clear_current_task(nullptr);
      finish_result(
        goal_handle,
        false,
        ExecuteTask::Goal::STAGE_FAILED,
        ExecuteTask::Result::ERROR_EXECUTION_FAILED,
        std::string("MTC task failed: ") + exception.what());
    }
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
    if (achieved_fraction < 0.99) {
      error_message =
        "Explicit lift Cartesian path only achieved fraction " +
        std::to_string(achieved_fraction);
      return false;
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
    constexpr double kCloseStepJoint7 = 0.0030;
    constexpr double kContactPreloadJoint7 = 0.0015;
    constexpr double kReachTolerance = 0.0006;
    constexpr double kProgressEpsilon = 0.0002;
    constexpr double kCommandDurationSec = 0.15;
    constexpr double kStepTimeoutSec = 0.8;
    constexpr double kStallTimeoutSec = 0.20;
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

  void publish_gripper_target(double joint7_target, double duration_sec)
  {
    auto message = trajectory_msgs::msg::JointTrajectory();
    message.joint_names = {"joint7"};

    auto point = trajectory_msgs::msg::JointTrajectoryPoint();
    point.positions = {std::clamp(joint7_target, 0.0, 0.035)};
    point.time_from_start = rclcpp::Duration::from_seconds(duration_sec);
    message.points.push_back(std::move(point));

    gripper_command_publisher_->publish(message);
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
      arm_move_group_->attachObject(parameters_.pickup_block.id, parameters_.hand_frame) :
      arm_move_group_->attachObject(
      parameters_.pickup_block.id,
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
      parameters_.pickup_block.id.c_str(),
      parameters_.hand_frame.c_str());
    return true;
  }

  void detach_pick_object_from_moveit()
  {
    arm_move_group_->detachObject(parameters_.pickup_block.id);
  }

  bool attach_pick_object_with_gazebo_link_attacher(std::string & error_message)
  {
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
  }

  void detach_pick_object_from_gazebo_link_attacher()
  {
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
  }

  bool gazebo_link_attached()
  {
    std::lock_guard<std::mutex> lock(gazebo_attachment_mutex_);
    return gazebo_block_attached_;
  }

  TaskParameters parameters_;
  std::unique_ptr<TaskFactory> factory_;
  std::unique_ptr<SceneManager> scene_manager_;
  std::unique_ptr<moveit::planning_interface::MoveGroupInterface> arm_move_group_;
  std::unique_ptr<moveit::planning_interface::MoveGroupInterface> gripper_move_group_;
  rclcpp::CallbackGroup::SharedPtr action_callback_group_;
  rclcpp::CallbackGroup::SharedPtr gazebo_callback_group_;
  rclcpp_action::Server<ExecuteTask>::SharedPtr action_server_;
  rclcpp::Client<AttachLink>::SharedPtr gazebo_attach_link_client_;
  rclcpp::Client<DetachLink>::SharedPtr gazebo_detach_link_client_;
  rclcpp::Subscription<sensor_msgs::msg::JointState>::SharedPtr joint_state_subscription_;
  rclcpp::Publisher<trajectory_msgs::msg::JointTrajectory>::SharedPtr gripper_command_publisher_;
  rclcpp::TimerBase::SharedPtr autostart_timer_;
  std::mutex current_task_mutex_;
  std::mutex gazebo_attachment_mutex_;
  std::mutex gripper_hold_mutex_;
  mtc::Task * current_task_{nullptr};
  bool active_goal_{false};
  bool gazebo_block_attached_{false};
  bool have_joint7_position_{false};
  bool gripper_hold_active_{false};
  double gripper_hold_target_{0.0};
  double latest_joint7_position_{0.0};
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
