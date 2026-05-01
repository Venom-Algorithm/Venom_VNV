#include <atomic>
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstddef>
#include <future>
#include <functional>
#include <map>
#include <memory>
#include <mutex>
#include <string>
#include <thread>
#include <utility>
#include <vector>

#include <controller_manager_msgs/srv/list_controllers.hpp>
#include <control_msgs/action/follow_joint_trajectory.hpp>
#include <gazebo_msgs/msg/entity_state.hpp>
#include <gazebo_msgs/srv/get_entity_state.hpp>
#include <gazebo_msgs/srv/set_entity_state.hpp>
#include <geometry_msgs/msg/pose_stamped.hpp>
#include <moveit/move_group_interface/move_group_interface.h>
#include <moveit/planning_scene_interface/planning_scene_interface.h>
#include <moveit_msgs/msg/collision_object.hpp>
#include <shape_msgs/msg/solid_primitive.hpp>
#include <rclcpp/rclcpp.hpp>
#include <rclcpp_action/rclcpp_action.hpp>
#include <tf2/LinearMath/Quaternion.h>
#include <tf2/LinearMath/Vector3.h>
#include <tf2_geometry_msgs/tf2_geometry_msgs.hpp>
#include <venom_manipulation_interfaces/action/execute_task.hpp>

class ManipulationCommander : public rclcpp::Node
{
public:
  using ExecuteTask = venom_manipulation_interfaces::action::ExecuteTask;
  using GoalHandleExecuteTask = rclcpp_action::ServerGoalHandle<ExecuteTask>;
  using ListControllers = controller_manager_msgs::srv::ListControllers;
  using GetEntityState = gazebo_msgs::srv::GetEntityState;
  using SetEntityState = gazebo_msgs::srv::SetEntityState;

  explicit ManipulationCommander(const rclcpp::NodeOptions & options = rclcpp::NodeOptions())
  : Node("manipulation_commander", options)
  {
    declare_parameters();

    action_server_ = rclcpp_action::create_server<ExecuteTask>(
      this,
      "/manipulation/execute_task",
      std::bind(&ManipulationCommander::handle_goal, this, std::placeholders::_1, std::placeholders::_2),
      std::bind(&ManipulationCommander::handle_cancel, this, std::placeholders::_1),
      std::bind(&ManipulationCommander::handle_accepted, this, std::placeholders::_1));
  }

  bool initialize()
  {
    planning_frame_ = get_parameter("planning_frame").as_string();
    arm_group_name_ = get_parameter("arm_group_name").as_string();
    gripper_group_name_ = get_parameter("gripper_group_name").as_string();
    arm_end_effector_link_ = get_parameter("arm_end_effector_link").as_string();
    arm_velocity_scaling_ = get_parameter("arm_velocity_scaling").as_double();
    arm_acceleration_scaling_ = get_parameter("arm_acceleration_scaling").as_double();
    gripper_velocity_scaling_ = get_parameter("gripper_velocity_scaling").as_double();
    gripper_acceleration_scaling_ = get_parameter("gripper_acceleration_scaling").as_double();
    arm_planning_time_sec_ = get_parameter("arm_planning_time_sec").as_double();
    gripper_planning_time_sec_ = get_parameter("gripper_planning_time_sec").as_double();
    arm_execution_timeout_sec_ = get_parameter("arm_execution_timeout_sec").as_double();
    gripper_execution_timeout_sec_ = get_parameter("gripper_execution_timeout_sec").as_double();
    controller_ready_timeout_sec_ = get_parameter("controller_ready_timeout_sec").as_double();
    post_grasp_settle_sec_ = get_parameter("post_grasp_settle_sec").as_double();
    post_release_settle_sec_ = get_parameter("post_release_settle_sec").as_double();
    grasp_candidate_planning_time_sec_ = get_parameter("grasp_candidate_planning_time_sec").as_double();
    enable_gazebo_attachment_ = get_parameter("enable_gazebo_attachment").as_bool();
    gazebo_attachment_frame_ = get_parameter("gazebo_attachment_frame").as_string();
    gazebo_attach_update_hz_ = get_parameter("gazebo_attach_update_hz").as_double();
    gazebo_service_timeout_sec_ = get_parameter("gazebo_service_timeout_sec").as_double();
    enable_scene_objects_ = get_parameter("enable_scene_objects").as_bool();
    enable_pickup_stand_collision_ = get_parameter("enable_pickup_stand_collision").as_bool();
    enable_place_stand_collision_ = get_parameter("enable_place_stand_collision").as_bool();
    generate_pick_targets_from_block_ = get_parameter("generate_pick_targets_from_block").as_bool();
    gripper_open_joint7_ = get_parameter("gripper_open_joint7").as_double();
    gripper_close_joint7_ = get_parameter("gripper_close_joint7").as_double();
    arm_controller_action_name_ = get_parameter("arm_controller_action_name").as_string();
    gripper_controller_action_name_ = get_parameter("gripper_controller_action_name").as_string();
    autostart_task_type_ = get_parameter("autostart_task_type").as_int();

    std::string error_message;
    if (!load_pose_parameter("home_pose", home_pose_, error_message) ||
      !load_pose_parameter("pregrasp_pose", pregrasp_pose_, error_message) ||
      !load_pose_parameter("grasp_pose", grasp_pose_, error_message) ||
      !load_pose_parameter("lift_pose", lift_pose_, error_message) ||
      !load_pose_parameter("place_pose", place_pose_, error_message))
    {
      initialization_error_ = error_message;
      RCLCPP_ERROR(get_logger(), "%s", initialization_error_.c_str());
      return false;
    }

    if (!load_joint_parameter("home_joints", home_target_.joints, error_message) ||
      !load_joint_parameter("pregrasp_joints", pregrasp_target_.joints, error_message) ||
      !load_joint_parameter("grasp_joints", grasp_target_.joints, error_message) ||
      !load_joint_parameter("lift_joints", lift_target_.joints, error_message) ||
      !load_joint_parameter("place_joints", place_target_.joints, error_message))
    {
      initialization_error_ = error_message;
      RCLCPP_ERROR(get_logger(), "%s", initialization_error_.c_str());
      return false;
    }

    home_target_.pose = home_pose_;
    pregrasp_target_.pose = pregrasp_pose_;
    grasp_target_.pose = grasp_pose_;
    lift_target_.pose = lift_pose_;
    place_target_.pose = place_pose_;
    transit_target_ = home_target_;

    auto node_base = std::static_pointer_cast<rclcpp::Node>(shared_from_this());
    arm_move_group_ = std::make_unique<moveit::planning_interface::MoveGroupInterface>(
      node_base, arm_group_name_);
    gripper_move_group_ = std::make_unique<moveit::planning_interface::MoveGroupInterface>(
      node_base, gripper_group_name_);
    arm_controller_client_ =
      rclcpp_action::create_client<control_msgs::action::FollowJointTrajectory>(
      node_base, arm_controller_action_name_);
    gripper_controller_client_ =
      rclcpp_action::create_client<control_msgs::action::FollowJointTrajectory>(
      node_base, gripper_controller_action_name_);
    controller_manager_client_ = create_client<ListControllers>("/controller_manager/list_controllers");
    gazebo_get_entity_state_client_ = create_client<GetEntityState>("/gazebo/get_entity_state");
    gazebo_set_entity_state_client_ = create_client<SetEntityState>("/gazebo/set_entity_state");
    planning_scene_interface_ =
      std::make_unique<moveit::planning_interface::PlanningSceneInterface>();

    arm_move_group_->setPoseReferenceFrame(planning_frame_);
    arm_move_group_->setPlanningTime(arm_planning_time_sec_);
    arm_move_group_->setMaxVelocityScalingFactor(arm_velocity_scaling_);
    arm_move_group_->setMaxAccelerationScalingFactor(arm_acceleration_scaling_);
    if (!arm_end_effector_link_.empty() &&
      !arm_move_group_->setEndEffectorLink(arm_end_effector_link_))
    {
      initialization_error_ =
        "Failed to set arm end effector link to '" + arm_end_effector_link_ + "'";
      RCLCPP_ERROR(get_logger(), "%s", initialization_error_.c_str());
      return false;
    }

    gripper_move_group_->setPlanningTime(gripper_planning_time_sec_);
    gripper_move_group_->setMaxVelocityScalingFactor(gripper_velocity_scaling_);
    gripper_move_group_->setMaxAccelerationScalingFactor(gripper_acceleration_scaling_);

    pickup_stand_box_.id = "pickup_stand_box";
    pickup_stand_box_.x = get_parameter("pickup_stand.x").as_double();
    pickup_stand_box_.y = get_parameter("pickup_stand.y").as_double();
    pickup_stand_box_.z = get_parameter("pickup_stand.z").as_double();
    pickup_stand_box_.size_x = get_parameter("pickup_stand.size_x").as_double();
    pickup_stand_box_.size_y = get_parameter("pickup_stand.size_y").as_double();
    pickup_stand_box_.size_z = get_parameter("pickup_stand.size_z").as_double();

    place_stand_box_.id = "place_stand_box";
    place_stand_box_.x = get_parameter("place_stand.x").as_double();
    place_stand_box_.y = get_parameter("place_stand.y").as_double();
    place_stand_box_.z = get_parameter("place_stand.z").as_double();
    place_stand_box_.size_x = get_parameter("place_stand.size_x").as_double();
    place_stand_box_.size_y = get_parameter("place_stand.size_y").as_double();
    place_stand_box_.size_z = get_parameter("place_stand.size_z").as_double();

    pickup_block_box_.id = get_parameter("pickup_block.id").as_string();
    pickup_block_box_.x = get_parameter("pickup_block.x").as_double();
    pickup_block_box_.y = get_parameter("pickup_block.y").as_double();
    pickup_block_box_.z = get_parameter("pickup_block.z").as_double();
    pickup_block_box_.size_x = get_parameter("pickup_block.size_x").as_double();
    pickup_block_box_.size_y = get_parameter("pickup_block.size_y").as_double();
    pickup_block_box_.size_z = get_parameter("pickup_block.size_z").as_double();
    attached_block_touch_links_ = get_parameter("pickup_block.touch_links").as_string_array();

    if (generate_pick_targets_from_block_) {
      pregrasp_target_.joints.clear();
      grasp_target_.joints.clear();
      lift_target_.joints.clear();

      if (!load_xyz_parameter("pick_target_orientation_rpy", pick_target_orientation_rpy_, error_message) ||
        !load_xyz_parameter("pregrasp_offset_xyz", pregrasp_offset_xyz_, error_message) ||
        !load_xyz_parameter("grasp_offset_xyz", grasp_offset_xyz_, error_message) ||
        !load_xyz_parameter("lift_offset_xyz", lift_offset_xyz_, error_message) ||
        !load_xyz_parameter("transit_offset_xyz", transit_offset_xyz_, error_message) ||
        !load_xyz_parameter("tcp_offset_xyz", tcp_offset_xyz_, error_message))
      {
        initialization_error_ = error_message;
        RCLCPP_ERROR(get_logger(), "%s", initialization_error_.c_str());
        return false;
      }

      top_grasp_candidate_yaws_ = get_parameter("top_grasp_candidate_yaws").as_double_array();
      if (top_grasp_candidate_yaws_.empty()) {
        top_grasp_candidate_yaws_.push_back(pick_target_orientation_rpy_.z);
      }

      generate_pick_targets_from_block();
    }

    if (enable_scene_objects_) {
      apply_scene_objects(false);
    }

    if (autostart_task_type_ > 0) {
      autostart_timer_ = create_wall_timer(
        std::chrono::seconds(2),
        std::bind(&ManipulationCommander::run_autostart_task, this));
    }

    const auto clock_type =
      get_clock()->get_clock_type() == RCL_ROS_TIME ? "ros_time" : "system_time";

    RCLCPP_INFO(
      get_logger(),
      "Initialized manipulation commander with planning frame '%s', arm group '%s', gripper group '%s', end effector '%s', clock '%s'",
      planning_frame_.c_str(), arm_group_name_.c_str(), gripper_group_name_.c_str(),
      arm_end_effector_link_.c_str(), clock_type);
    return true;
  }

private:
  struct PoseTarget
  {
    double x;
    double y;
    double z;
    double roll;
    double pitch;
    double yaw;
  };

  struct XYZ
  {
    double x;
    double y;
    double z;
  };

  struct ArmTarget
  {
    PoseTarget pose{};
    std::vector<double> joints;
  };

  struct PickTargets
  {
    ArmTarget pregrasp;
    ArmTarget grasp;
    ArmTarget lift;
    ArmTarget transit;
    PoseTarget pregrasp_tcp{};
    PoseTarget grasp_tcp{};
    PoseTarget lift_tcp{};
    PoseTarget transit_tcp{};
    double yaw{0.0};
  };

  struct SceneBox
  {
    std::string id;
    double x{0.0};
    double y{0.0};
    double z{0.0};
    double size_x{0.0};
    double size_y{0.0};
    double size_z{0.0};
  };

  enum class Stage : uint8_t
  {
    IDLE = ExecuteTask::Goal::STAGE_IDLE,
    MOVING_HOME = ExecuteTask::Goal::STAGE_MOVING_HOME,
    MOVING_PREGRASP = ExecuteTask::Goal::STAGE_MOVING_PREGRASP,
    MOVING_GRASP = ExecuteTask::Goal::STAGE_MOVING_GRASP,
    CLOSING_GRIPPER = ExecuteTask::Goal::STAGE_CLOSING_GRIPPER,
    LIFTING = ExecuteTask::Goal::STAGE_LIFTING,
    MOVING_PLACE = ExecuteTask::Goal::STAGE_MOVING_PLACE,
    OPENING_GRIPPER = ExecuteTask::Goal::STAGE_OPENING_GRIPPER,
    DONE = ExecuteTask::Goal::STAGE_DONE,
    FAILED = ExecuteTask::Goal::STAGE_FAILED,
  };

  enum class ErrorCode : int32_t
  {
    NONE = ExecuteTask::Result::ERROR_NONE,
    NOT_READY = ExecuteTask::Result::ERROR_NOT_READY,
    INVALID_TASK = ExecuteTask::Result::ERROR_INVALID_TASK,
    PLAN_FAILED = ExecuteTask::Result::ERROR_PLAN_FAILED,
    EXECUTION_FAILED = ExecuteTask::Result::ERROR_EXECUTION_FAILED,
    TIMEOUT = ExecuteTask::Result::ERROR_TIMEOUT,
    CANCELED = ExecuteTask::Result::ERROR_CANCELED,
  };

  void declare_parameters()
  {
    declare_parameter<std::string>("planning_frame", "world");
    declare_parameter<std::string>("arm_group_name", "arm");
    declare_parameter<std::string>("gripper_group_name", "gripper");
    declare_parameter<std::string>("arm_end_effector_link", "gripper_grasp_center");
    declare_parameter<double>("arm_velocity_scaling", 0.2);
    declare_parameter<double>("arm_acceleration_scaling", 0.2);
    declare_parameter<double>("gripper_velocity_scaling", 0.8);
    declare_parameter<double>("gripper_acceleration_scaling", 0.8);
    declare_parameter<double>("arm_planning_time_sec", 5.0);
    declare_parameter<double>("gripper_planning_time_sec", 3.0);
    declare_parameter<double>("arm_execution_timeout_sec", 15.0);
    declare_parameter<double>("gripper_execution_timeout_sec", 8.0);
    declare_parameter<double>("controller_ready_timeout_sec", 30.0);
    declare_parameter<double>("post_grasp_settle_sec", 0.7);
    declare_parameter<double>("post_release_settle_sec", 0.4);
    declare_parameter<bool>("enable_gazebo_attachment", false);
    declare_parameter<std::string>("gazebo_attachment_frame", "gripper_grasp_center");
    declare_parameter<double>("gazebo_attach_update_hz", 30.0);
    declare_parameter<double>("gazebo_service_timeout_sec", 3.0);
    declare_parameter<bool>("enable_scene_objects", true);
    declare_parameter<bool>("enable_pickup_stand_collision", false);
    declare_parameter<bool>("enable_place_stand_collision", true);
    declare_parameter<bool>("generate_pick_targets_from_block", false);
    declare_parameter<double>("pickup_stand.x", 0.281);
    declare_parameter<double>("pickup_stand.y", 0.0);
    declare_parameter<double>("pickup_stand.z", 0.2165);
    declare_parameter<double>("pickup_stand.size_x", 0.012);
    declare_parameter<double>("pickup_stand.size_y", 0.012);
    declare_parameter<double>("pickup_stand.size_z", 0.433);
    declare_parameter<double>("place_stand.x", 0.175);
    declare_parameter<double>("place_stand.y", 0.107);
    declare_parameter<double>("place_stand.z", 0.2165);
    declare_parameter<double>("place_stand.size_x", 0.012);
    declare_parameter<double>("place_stand.size_y", 0.012);
    declare_parameter<double>("place_stand.size_z", 0.433);
    declare_parameter<std::string>("pickup_block.id", "pick_target_block");
    declare_parameter<double>("pickup_block.x", 0.281);
    declare_parameter<double>("pickup_block.y", 0.0);
    declare_parameter<double>("pickup_block.z", 0.453);
    declare_parameter<double>("pickup_block.size_x", 0.018);
    declare_parameter<double>("pickup_block.size_y", 0.018);
    declare_parameter<double>("pickup_block.size_z", 0.035);
    declare_parameter<std::vector<std::string>>(
      "pickup_block.touch_links", std::vector<std::string>{"link7", "link8"});
    declare_parameter<std::vector<double>>(
      "pick_target_orientation_rpy", std::vector<double>{3.14159, 0.0, -1.5708});
    declare_parameter<std::vector<double>>(
      "top_grasp_candidate_yaws", std::vector<double>{0.0, 1.5708, -1.5708, 3.14159});
    declare_parameter<std::vector<double>>(
      "pregrasp_offset_xyz", std::vector<double>{0.0, 0.0, 0.04});
    declare_parameter<std::vector<double>>(
      "grasp_offset_xyz", std::vector<double>{0.0, 0.0, -0.005});
    declare_parameter<std::vector<double>>(
      "lift_offset_xyz", std::vector<double>{0.0, 0.0, 0.07});
    declare_parameter<std::vector<double>>(
      "transit_offset_xyz", std::vector<double>{-0.10, 0.0, 0.16});
    declare_parameter<std::vector<double>>(
      "tcp_offset_xyz", std::vector<double>{0.0, 0.0, 0.0});
    declare_parameter<double>("grasp_candidate_planning_time_sec", 5.0);
    declare_parameter<std::vector<double>>("home_pose", std::vector<double>{0.25, 0.0, 0.35, 3.14159, 0.0, 0.0});
    declare_parameter<std::vector<double>>(
      "pregrasp_pose", std::vector<double>{0.28, -0.10, 0.22, 3.14159, 0.0, -1.5708});
    declare_parameter<std::vector<double>>(
      "grasp_pose", std::vector<double>{0.28, -0.10, 0.14, 3.14159, 0.0, -1.5708});
    declare_parameter<std::vector<double>>(
      "lift_pose", std::vector<double>{0.28, -0.10, 0.28, 3.14159, 0.0, -1.5708});
    declare_parameter<std::vector<double>>(
      "place_pose", std::vector<double>{0.28, 0.12, 0.22, 3.14159, 0.0, 1.5708});
    declare_parameter<std::vector<double>>("home_joints", std::vector<double>{});
    declare_parameter<std::vector<double>>("pregrasp_joints", std::vector<double>{});
    declare_parameter<std::vector<double>>("grasp_joints", std::vector<double>{});
    declare_parameter<std::vector<double>>("lift_joints", std::vector<double>{});
    declare_parameter<std::vector<double>>("place_joints", std::vector<double>{});
    declare_parameter<double>("gripper_open_joint7", 0.03);
    declare_parameter<double>("gripper_close_joint7", 0.005);
    declare_parameter<std::string>("arm_controller_action_name", "arm_controller/follow_joint_trajectory");
    declare_parameter<std::string>("gripper_controller_action_name", "gripper_controller/follow_joint_trajectory");
    declare_parameter<int64_t>("autostart_task_type", 0);
  }

  bool load_pose_parameter(
    const std::string & name, PoseTarget & out_pose, std::string & error_message)
  {
    const auto values = get_parameter(name).as_double_array();
    if (values.size() != 6) {
      error_message = "Parameter '" + name + "' must contain exactly 6 values [x, y, z, roll, pitch, yaw]";
      return false;
    }

    out_pose = PoseTarget{
      values[0], values[1], values[2], values[3], values[4], values[5]};
    return true;
  }

  bool load_joint_parameter(
    const std::string & name, std::vector<double> & out_joints, std::string & error_message)
  {
    rclcpp::Parameter parameter;
    if (!get_parameter(name, parameter) ||
      parameter.get_type() == rclcpp::ParameterType::PARAMETER_NOT_SET)
    {
      out_joints.clear();
      return true;
    }

    const auto values = parameter.as_double_array();
    if (!values.empty() && values.size() != arm_joint_names_.size()) {
      error_message =
        "Parameter '" + name + "' must contain exactly " + std::to_string(arm_joint_names_.size()) +
        " joint values or remain empty";
      return false;
    }

    out_joints = values;
    return true;
  }

  bool load_xyz_parameter(
    const std::string & name, XYZ & out_xyz, std::string & error_message)
  {
    const auto values = get_parameter(name).as_double_array();
    if (values.size() != 3) {
      error_message = "Parameter '" + name + "' must contain exactly 3 values [x, y, z]";
      return false;
    }

    out_xyz = XYZ{values[0], values[1], values[2]};
    return true;
  }

  void generate_pick_targets_from_block()
  {
    const auto targets = build_pick_targets_from_block(pick_target_orientation_rpy_.z);
    assign_pick_targets(targets);
    log_pick_targets("Generated initial pick targets", targets);
  }

  PoseTarget compensate_tcp_pose(const PoseTarget & tcp_pose) const
  {
    tf2::Quaternion quaternion;
    quaternion.setRPY(tcp_pose.roll, tcp_pose.pitch, tcp_pose.yaw);

    const tf2::Vector3 tcp_offset(
      tcp_offset_xyz_.x,
      tcp_offset_xyz_.y,
      tcp_offset_xyz_.z);
    const tf2::Vector3 rotated_offset = tf2::quatRotate(quaternion, tcp_offset);

    return PoseTarget{
      tcp_pose.x - rotated_offset.x(),
      tcp_pose.y - rotated_offset.y(),
      tcp_pose.z - rotated_offset.z(),
      tcp_pose.roll,
      tcp_pose.pitch,
      tcp_pose.yaw};
  }

  PickTargets build_pick_targets_from_block(double yaw) const
  {
    const double block_top_z = pickup_block_box_.z + (pickup_block_box_.size_z * 0.5);
    const auto make_tcp_pose = [this, block_top_z, yaw](const XYZ & offset) {
      return PoseTarget{
        pickup_block_box_.x + offset.x,
        pickup_block_box_.y + offset.y,
        block_top_z + offset.z,
        pick_target_orientation_rpy_.x,
        pick_target_orientation_rpy_.y,
        yaw};
    };

    PickTargets targets;
    targets.yaw = yaw;
    targets.pregrasp_tcp = make_tcp_pose(pregrasp_offset_xyz_);
    targets.grasp_tcp = make_tcp_pose(grasp_offset_xyz_);
    targets.lift_tcp = make_tcp_pose(lift_offset_xyz_);
    targets.transit_tcp = make_tcp_pose(transit_offset_xyz_);

    targets.pregrasp.pose = compensate_tcp_pose(targets.pregrasp_tcp);
    targets.grasp.pose = compensate_tcp_pose(targets.grasp_tcp);
    targets.lift.pose = compensate_tcp_pose(targets.lift_tcp);
    targets.transit.pose = compensate_tcp_pose(targets.transit_tcp);

    return targets;
  }

  void assign_pick_targets(const PickTargets & targets)
  {
    pregrasp_target_ = targets.pregrasp;
    grasp_target_ = targets.grasp;
    lift_target_ = targets.lift;
    transit_target_ = targets.transit;

    pregrasp_target_.joints.clear();
    grasp_target_.joints.clear();
    lift_target_.joints.clear();
    transit_target_.joints.clear();
  }

  void log_pick_targets(const std::string & prefix, const PickTargets & targets) const
  {
    RCLCPP_INFO(
      get_logger(),
      "%s yaw=%.3f tcp: pregrasp=(%.3f, %.3f, %.3f) grasp=(%.3f, %.3f, %.3f) lift=(%.3f, %.3f, %.3f) transit=(%.3f, %.3f, %.3f)",
      prefix.c_str(), targets.yaw,
      targets.pregrasp_tcp.x, targets.pregrasp_tcp.y, targets.pregrasp_tcp.z,
      targets.grasp_tcp.x, targets.grasp_tcp.y, targets.grasp_tcp.z,
      targets.lift_tcp.x, targets.lift_tcp.y, targets.lift_tcp.z,
      targets.transit_tcp.x, targets.transit_tcp.y, targets.transit_tcp.z);
    RCLCPP_INFO(
      get_logger(),
      "%s yaw=%.3f arm: pregrasp=(%.3f, %.3f, %.3f) grasp=(%.3f, %.3f, %.3f) lift=(%.3f, %.3f, %.3f) transit=(%.3f, %.3f, %.3f)",
      prefix.c_str(), targets.yaw,
      targets.pregrasp.pose.x, targets.pregrasp.pose.y, targets.pregrasp.pose.z,
      targets.grasp.pose.x, targets.grasp.pose.y, targets.grasp.pose.z,
      targets.lift.pose.x, targets.lift.pose.y, targets.lift.pose.z,
      targets.transit.pose.x, targets.transit.pose.y, targets.transit.pose.z);
  }

  geometry_msgs::msg::PoseStamped to_pose_stamped(const PoseTarget & pose_target) const
  {
    geometry_msgs::msg::PoseStamped pose_stamped;
    pose_stamped.header.frame_id = planning_frame_;
    pose_stamped.pose.position.x = pose_target.x;
    pose_stamped.pose.position.y = pose_target.y;
    pose_stamped.pose.position.z = pose_target.z;

    tf2::Quaternion quaternion;
    quaternion.setRPY(pose_target.roll, pose_target.pitch, pose_target.yaw);
    pose_stamped.pose.orientation = tf2::toMsg(quaternion);
    return pose_stamped;
  }

  bool prepare_arm_pose_target(const PoseTarget & pose_target, Stage stage, bool log_approximate_ik)
  {
    const auto pose_stamped = to_pose_stamped(pose_target);

    arm_move_group_->clearPoseTargets();
    arm_move_group_->setStartStateToCurrentState();
    const bool approximate_target_set =
      arm_move_group_->setApproximateJointValueTarget(pose_stamped, arm_end_effector_link_);

    if (!approximate_target_set) {
      RCLCPP_WARN(
        get_logger(),
        "Approximate IK target failed for stage %u at pose (%.3f, %.3f, %.3f); falling back to exact pose target",
        static_cast<unsigned int>(stage), pose_target.x, pose_target.y, pose_target.z);
      arm_move_group_->setPoseTarget(pose_stamped, arm_end_effector_link_);
      return false;
    }

    if (log_approximate_ik) {
      RCLCPP_INFO(
        get_logger(),
        "Using approximate IK target for stage %u at pose (%.3f, %.3f, %.3f)",
        static_cast<unsigned int>(stage), pose_target.x, pose_target.y, pose_target.z);
    }
    return true;
  }

  bool can_plan_arm_pose(const PoseTarget & pose_target, Stage stage, std::string & error_message)
  {
    if (!ensure_current_state(error_message)) {
      return false;
    }

    arm_move_group_->setPlanningTime(grasp_candidate_planning_time_sec_);
    prepare_arm_pose_target(pose_target, stage, false);

    moveit::planning_interface::MoveGroupInterface::Plan plan;
    const bool plan_success = static_cast<bool>(arm_move_group_->plan(plan));
    arm_move_group_->clearPoseTargets();
    arm_move_group_->setPlanningTime(arm_planning_time_sec_);

    if (!plan_success) {
      error_message = "Candidate pose planning failed";
      return false;
    }
    return true;
  }

  bool select_pick_targets(
    const std::shared_ptr<GoalHandleExecuteTask> & goal_handle,
    ExecuteTask::Result & result,
    std::string & error_message)
  {
    if (!generate_pick_targets_from_block_) {
      return true;
    }

    publish_feedback(goal_handle, Stage::IDLE, "Selecting feasible top grasp candidate");

    std::string last_error = "No grasp candidate evaluated";
    for (const double yaw : top_grasp_candidate_yaws_) {
      if (check_cancel(goal_handle, result)) {
        error_message = "Task canceled";
        return false;
      }

      const auto candidate = build_pick_targets_from_block(yaw);
      log_pick_targets("Evaluating pick target candidate", candidate);

      std::string candidate_error;
      if (!can_plan_arm_pose(candidate.pregrasp.pose, Stage::MOVING_PREGRASP, candidate_error)) {
        last_error = "pregrasp not feasible at yaw " + std::to_string(yaw) + ": " + candidate_error;
        RCLCPP_WARN(get_logger(), "%s", last_error.c_str());
        continue;
      }
      if (!can_plan_arm_pose(candidate.grasp.pose, Stage::MOVING_GRASP, candidate_error)) {
        last_error = "grasp not feasible at yaw " + std::to_string(yaw) + ": " + candidate_error;
        RCLCPP_WARN(get_logger(), "%s", last_error.c_str());
        continue;
      }

      assign_pick_targets(candidate);
      RCLCPP_INFO(get_logger(), "Selected top grasp candidate yaw=%.3f", yaw);
      return true;
    }

    error_message = "No feasible top grasp candidate found: " + last_error;
    set_result(result, Stage::MOVING_PREGRASP, ErrorCode::PLAN_FAILED, error_message);
    return false;
  }

  rclcpp_action::GoalResponse handle_goal(
    const rclcpp_action::GoalUUID &,
    std::shared_ptr<const ExecuteTask::Goal> goal)
  {
    if (!initialized_) {
      RCLCPP_WARN(get_logger(), "Rejecting manipulation goal: commander not initialized");
      return rclcpp_action::GoalResponse::REJECT;
    }

    if (goal->task_type != ExecuteTask::Goal::PICK_AND_PLACE_FIXED &&
      goal->task_type != ExecuteTask::Goal::MOVE_HOME)
    {
      RCLCPP_WARN(get_logger(), "Rejecting manipulation goal: invalid task type %u", goal->task_type);
      return rclcpp_action::GoalResponse::REJECT;
    }

    if (busy_.load()) {
      RCLCPP_WARN(get_logger(), "Rejecting manipulation goal: commander is busy");
      return rclcpp_action::GoalResponse::REJECT;
    }

    return rclcpp_action::GoalResponse::ACCEPT_AND_EXECUTE;
  }

  rclcpp_action::CancelResponse handle_cancel(const std::shared_ptr<GoalHandleExecuteTask> goal_handle)
  {
    (void)goal_handle;
    RCLCPP_INFO(get_logger(), "Received manipulation cancel request");
    stop_motion();
    return rclcpp_action::CancelResponse::ACCEPT;
  }

  void handle_accepted(const std::shared_ptr<GoalHandleExecuteTask> goal_handle)
  {
    busy_.store(true);
    std::thread{std::bind(&ManipulationCommander::execute_goal, this, goal_handle)}.detach();
  }

  void execute_goal(const std::shared_ptr<GoalHandleExecuteTask> goal_handle)
  {
    auto result = std::make_shared<ExecuteTask::Result>();
    result->success = false;
    result->stage_reached = static_cast<uint8_t>(Stage::IDLE);
    result->error_code = static_cast<int32_t>(ErrorCode::NONE);

    if (!initialized_) {
      set_result(*result, Stage::FAILED, ErrorCode::NOT_READY, initialization_error_);
      goal_handle->abort(result);
      busy_.store(false);
      return;
    }

    std::string error_message;
    if (!wait_for_execution_servers(goal_handle, *result, error_message)) {
      set_result(*result, Stage::FAILED, ErrorCode::NOT_READY, error_message);
      goal_handle->abort(result);
      busy_.store(false);
      return;
    }

    bool success = false;
    const auto task_type = goal_handle->get_goal()->task_type;
    if (task_type == ExecuteTask::Goal::PICK_AND_PLACE_FIXED) {
      success = run_pick_and_place(goal_handle, *result, error_message);
    } else if (task_type == ExecuteTask::Goal::MOVE_HOME) {
      success = move_arm(goal_handle, Stage::MOVING_HOME, home_target_, arm_execution_timeout_sec_, *result, error_message);
    } else {
      set_result(*result, Stage::FAILED, ErrorCode::INVALID_TASK, "Unsupported task type");
      goal_handle->abort(result);
      busy_.store(false);
      return;
    }

    if (goal_handle->is_canceling()) {
      set_result(*result, Stage::FAILED, ErrorCode::CANCELED, "Task canceled");
      goal_handle->canceled(result);
    } else if (!success) {
      if (result->error_code == static_cast<int32_t>(ErrorCode::NONE)) {
        set_result(*result, Stage::FAILED, ErrorCode::EXECUTION_FAILED, error_message);
      }
      goal_handle->abort(result);
    } else {
      set_result(*result, Stage::DONE, ErrorCode::NONE, "Task completed successfully");
      result->success = true;
      goal_handle->succeed(result);
    }

    busy_.store(false);
  }

  bool run_pick_and_place(
    const std::shared_ptr<GoalHandleExecuteTask> & goal_handle,
    ExecuteTask::Result & result,
    std::string & error_message)
  {
    if (enable_scene_objects_) {
      detach_pickup_block();
      apply_scene_objects(false);
    }

    return move_arm(goal_handle, Stage::MOVING_HOME, home_target_, arm_execution_timeout_sec_, result, error_message) &&
           move_gripper(goal_handle, Stage::OPENING_GRIPPER, gripper_open_joint7_, gripper_execution_timeout_sec_, result, error_message) &&
           select_pick_targets(goal_handle, result, error_message) &&
           move_arm(goal_handle, Stage::MOVING_PREGRASP, pregrasp_target_, arm_execution_timeout_sec_, result, error_message) &&
           move_arm(goal_handle, Stage::MOVING_GRASP, grasp_target_, arm_execution_timeout_sec_, result, error_message) &&
           move_gripper(goal_handle, Stage::CLOSING_GRIPPER, gripper_close_joint7_, gripper_execution_timeout_sec_, result, error_message) &&
           settle_after_action(goal_handle, Stage::CLOSING_GRIPPER, post_grasp_settle_sec_, "Waiting for grasp to settle", result, error_message) &&
           attach_pickup_block(result, error_message) &&
           move_arm(goal_handle, Stage::LIFTING, lift_target_, arm_execution_timeout_sec_, result, error_message) &&
           move_arm(goal_handle, Stage::MOVING_PLACE, transit_target_, arm_execution_timeout_sec_, result, error_message) &&
           move_arm(goal_handle, Stage::MOVING_PLACE, place_target_, arm_execution_timeout_sec_, result, error_message) &&
           move_gripper(goal_handle, Stage::OPENING_GRIPPER, gripper_open_joint7_, gripper_execution_timeout_sec_, result, error_message) &&
           detach_pickup_block() &&
           settle_after_action(goal_handle, Stage::OPENING_GRIPPER, post_release_settle_sec_, "Waiting for release to settle", result, error_message);
  }

  bool move_arm(
    const std::shared_ptr<GoalHandleExecuteTask> & goal_handle,
    Stage stage,
    const ArmTarget & arm_target,
    double execution_timeout_sec,
    ExecuteTask::Result & result,
    std::string & error_message)
  {
    if (!arm_target.joints.empty()) {
      return move_arm_to_joint_values(
        goal_handle, stage, arm_target.joints, execution_timeout_sec, result, error_message);
    }

    return move_arm_to_pose(
      goal_handle, stage, arm_target.pose, execution_timeout_sec, result, error_message);
  }

  bool move_arm_to_pose(
    const std::shared_ptr<GoalHandleExecuteTask> & goal_handle,
    Stage stage,
    const PoseTarget & pose_target,
    double execution_timeout_sec,
    ExecuteTask::Result & result,
    std::string & error_message)
  {
    if (!ensure_current_state(error_message)) {
      set_result(result, stage, ErrorCode::NOT_READY, error_message);
      return false;
    }
    if (check_cancel(goal_handle, result)) {
      error_message = "Task canceled";
      return false;
    }

    publish_feedback(goal_handle, stage, "Planning arm motion");

    prepare_arm_pose_target(pose_target, stage, true);

    moveit::planning_interface::MoveGroupInterface::Plan plan;
    const auto plan_start = std::chrono::steady_clock::now();
    const bool plan_success = static_cast<bool>(arm_move_group_->plan(plan));
    const auto plan_elapsed = std::chrono::duration<double>(std::chrono::steady_clock::now() - plan_start).count();

    if (!plan_success) {
      error_message = "Arm planning failed";
      set_result(result, stage, ErrorCode::PLAN_FAILED, error_message);
      return false;
    }
    if (plan_elapsed > arm_planning_time_sec_) {
      error_message = "Arm planning exceeded timeout";
      set_result(result, stage, ErrorCode::TIMEOUT, error_message);
      return false;
    }

    if (check_cancel(goal_handle, result)) {
      error_message = "Task canceled";
      return false;
    }

    publish_feedback(goal_handle, stage, "Executing arm motion");
    const auto exec_start = std::chrono::steady_clock::now();
    const bool exec_success = static_cast<bool>(arm_move_group_->execute(plan));
    const auto exec_elapsed = std::chrono::duration<double>(std::chrono::steady_clock::now() - exec_start).count();
    arm_move_group_->clearPoseTargets();

    if (!exec_success) {
      error_message = "Arm execution failed";
      set_result(result, stage, ErrorCode::EXECUTION_FAILED, error_message);
      return false;
    }
    if (exec_elapsed > execution_timeout_sec) {
      error_message = "Arm execution exceeded timeout";
      set_result(result, stage, ErrorCode::TIMEOUT, error_message);
      return false;
    }

    result.stage_reached = stage_to_result(stage);
    return true;
  }

  bool move_gripper(
    const std::shared_ptr<GoalHandleExecuteTask> & goal_handle,
    Stage stage,
    double joint7_target,
    double execution_timeout_sec,
    ExecuteTask::Result & result,
    std::string & error_message)
  {
    if (!ensure_current_state(error_message)) {
      set_result(result, stage, ErrorCode::NOT_READY, error_message);
      return false;
    }
    if (check_cancel(goal_handle, result)) {
      error_message = "Task canceled";
      return false;
    }

    publish_feedback(goal_handle, stage, "Planning gripper motion");

    std::map<std::string, double> target_map;
    target_map["joint7"] = joint7_target;

    gripper_move_group_->setStartStateToCurrentState();
    gripper_move_group_->setJointValueTarget(target_map);

    moveit::planning_interface::MoveGroupInterface::Plan plan;
    const auto plan_start = std::chrono::steady_clock::now();
    const bool plan_success = static_cast<bool>(gripper_move_group_->plan(plan));
    const auto plan_elapsed = std::chrono::duration<double>(std::chrono::steady_clock::now() - plan_start).count();

    if (!plan_success) {
      error_message = "Gripper planning failed";
      set_result(result, stage, ErrorCode::PLAN_FAILED, error_message);
      return false;
    }
    if (plan_elapsed > gripper_planning_time_sec_) {
      error_message = "Gripper planning exceeded timeout";
      set_result(result, stage, ErrorCode::TIMEOUT, error_message);
      return false;
    }

    if (check_cancel(goal_handle, result)) {
      error_message = "Task canceled";
      return false;
    }

    publish_feedback(goal_handle, stage, "Executing gripper motion");
    const auto exec_start = std::chrono::steady_clock::now();
    const bool exec_success = static_cast<bool>(gripper_move_group_->execute(plan));
    const auto exec_elapsed = std::chrono::duration<double>(std::chrono::steady_clock::now() - exec_start).count();

    if (!exec_success) {
      error_message = "Gripper execution failed";
      set_result(result, stage, ErrorCode::EXECUTION_FAILED, error_message);
      return false;
    }
    if (exec_elapsed > execution_timeout_sec) {
      error_message = "Gripper execution exceeded timeout";
      set_result(result, stage, ErrorCode::TIMEOUT, error_message);
      return false;
    }

    result.stage_reached = stage_to_result(stage);
    return true;
  }

  bool move_arm_to_joint_values(
    const std::shared_ptr<GoalHandleExecuteTask> & goal_handle,
    Stage stage,
    const std::vector<double> & joint_values,
    double execution_timeout_sec,
    ExecuteTask::Result & result,
    std::string & error_message)
  {
    if (!ensure_current_state(error_message)) {
      set_result(result, stage, ErrorCode::NOT_READY, error_message);
      return false;
    }
    if (check_cancel(goal_handle, result)) {
      error_message = "Task canceled";
      return false;
    }

    publish_feedback(goal_handle, stage, "Planning arm joint motion");

    std::map<std::string, double> target_map;
    for (std::size_t index = 0; index < arm_joint_names_.size(); ++index) {
      target_map[arm_joint_names_[index]] = joint_values[index];
    }

    arm_move_group_->clearPoseTargets();
    arm_move_group_->setStartStateToCurrentState();
    arm_move_group_->setJointValueTarget(target_map);

    moveit::planning_interface::MoveGroupInterface::Plan plan;
    const auto plan_start = std::chrono::steady_clock::now();
    const bool plan_success = static_cast<bool>(arm_move_group_->plan(plan));
    const auto plan_elapsed = std::chrono::duration<double>(std::chrono::steady_clock::now() - plan_start).count();

    if (!plan_success) {
      error_message = "Arm joint-space planning failed";
      set_result(result, stage, ErrorCode::PLAN_FAILED, error_message);
      return false;
    }
    if (plan_elapsed > arm_planning_time_sec_) {
      error_message = "Arm planning exceeded timeout";
      set_result(result, stage, ErrorCode::TIMEOUT, error_message);
      return false;
    }

    if (check_cancel(goal_handle, result)) {
      error_message = "Task canceled";
      return false;
    }

    publish_feedback(goal_handle, stage, "Executing arm joint motion");
    const auto exec_start = std::chrono::steady_clock::now();
    const bool exec_success = static_cast<bool>(arm_move_group_->execute(plan));
    const auto exec_elapsed = std::chrono::duration<double>(std::chrono::steady_clock::now() - exec_start).count();

    if (!exec_success) {
      error_message = "Arm joint-space execution failed";
      set_result(result, stage, ErrorCode::EXECUTION_FAILED, error_message);
      return false;
    }
    if (exec_elapsed > execution_timeout_sec) {
      error_message = "Arm execution exceeded timeout";
      set_result(result, stage, ErrorCode::TIMEOUT, error_message);
      return false;
    }

    result.stage_reached = stage_to_result(stage);
    return true;
  }

  bool settle_after_action(
    const std::shared_ptr<GoalHandleExecuteTask> & goal_handle,
    Stage stage,
    double wait_sec,
    const std::string & message,
    ExecuteTask::Result & result,
    std::string & error_message)
  {
    if (wait_sec <= 0.0) {
      return true;
    }
    if (check_cancel(goal_handle, result)) {
      error_message = "Task canceled";
      return false;
    }

    publish_feedback(goal_handle, stage, message);
    std::this_thread::sleep_for(std::chrono::duration<double>(wait_sec));

    if (check_cancel(goal_handle, result)) {
      error_message = "Task canceled";
      return false;
    }

    result.stage_reached = stage_to_result(stage);
    return true;
  }

  moveit_msgs::msg::CollisionObject make_box_collision_object(const SceneBox & box) const
  {
    moveit_msgs::msg::CollisionObject collision_object;
    collision_object.header.frame_id = planning_frame_;
    collision_object.id = box.id;

    shape_msgs::msg::SolidPrimitive primitive;
    primitive.type = shape_msgs::msg::SolidPrimitive::BOX;
    primitive.dimensions = {box.size_x, box.size_y, box.size_z};

    geometry_msgs::msg::Pose pose;
    pose.orientation.w = 1.0;
    pose.position.x = box.x;
    pose.position.y = box.y;
    pose.position.z = box.z;

    collision_object.primitives.push_back(primitive);
    collision_object.primitive_poses.push_back(pose);
    collision_object.operation = moveit_msgs::msg::CollisionObject::ADD;
    return collision_object;
  }

  void apply_scene_objects(bool include_pickup_block)
  {
    if (!planning_scene_interface_) {
      return;
    }

    std::vector<moveit_msgs::msg::CollisionObject> collision_objects;
    if (enable_pickup_stand_collision_) {
      collision_objects.push_back(make_box_collision_object(pickup_stand_box_));
    }
    if (enable_place_stand_collision_) {
      collision_objects.push_back(make_box_collision_object(place_stand_box_));
    }

    if (include_pickup_block && !pickup_block_attached_) {
      collision_objects.push_back(make_box_collision_object(pickup_block_box_));
    }

    planning_scene_interface_->applyCollisionObjects(collision_objects);
  }

  bool attach_pickup_block(ExecuteTask::Result & result, std::string & error_message)
  {
    if (!enable_scene_objects_ || pickup_block_attached_) {
      return true;
    }

    if (!arm_move_group_) {
      error_message = "Arm move group is not available for attach";
      set_result(result, Stage::CLOSING_GRIPPER, ErrorCode::NOT_READY, error_message);
      return false;
    }

    planning_scene_interface_->applyCollisionObject(make_box_collision_object(pickup_block_box_));
    arm_move_group_->attachObject(pickup_block_box_.id, "gripper_base", attached_block_touch_links_);

    if (enable_gazebo_attachment_ &&
      !start_gazebo_attachment(result, error_message))
    {
      arm_move_group_->detachObject(pickup_block_box_.id);
      return false;
    }

    pickup_block_attached_ = true;
    return true;
  }

  bool detach_pickup_block()
  {
    stop_gazebo_attachment();

    if (!enable_scene_objects_) {
      return true;
    }

    if (arm_move_group_ && pickup_block_attached_) {
      arm_move_group_->detachObject(pickup_block_box_.id);
    }
    pickup_block_attached_ = false;

    pickup_block_box_.x = get_parameter("pickup_block.x").as_double();
    pickup_block_box_.y = get_parameter("pickup_block.y").as_double();
    pickup_block_box_.z = get_parameter("pickup_block.z").as_double();

    std::vector<std::string> object_ids{
      pickup_stand_box_.id,
      place_stand_box_.id,
      pickup_block_box_.id,
    };
    planning_scene_interface_->removeCollisionObjects(object_ids);
    apply_scene_objects(false);
    return true;
  }

  bool start_gazebo_attachment(ExecuteTask::Result & result, std::string & error_message)
  {
    if (!gazebo_get_entity_state_client_ || !gazebo_set_entity_state_client_) {
      error_message = "Gazebo entity state clients are not available";
      set_result(result, Stage::CLOSING_GRIPPER, ErrorCode::NOT_READY, error_message);
      return false;
    }

    const auto timeout = std::chrono::duration<double>(gazebo_service_timeout_sec_);

    auto request = std::make_shared<GetEntityState::Request>();
    request->name = pickup_block_box_.id;
    request->reference_frame = gazebo_attachment_frame_;

    auto future = gazebo_get_entity_state_client_->async_send_request(request);
    if (future.wait_for(timeout) != std::future_status::ready) {
      error_message = "Timed out waiting for Gazebo entity state";
      set_result(result, Stage::CLOSING_GRIPPER, ErrorCode::TIMEOUT, error_message);
      return false;
    }

    const auto response = future.get();
    if (!response->success) {
      error_message =
        "Gazebo failed to provide pickup block state relative to '" + gazebo_attachment_frame_ + "'";
      set_result(result, Stage::CLOSING_GRIPPER, ErrorCode::EXECUTION_FAILED, error_message);
      return false;
    }

    {
      std::scoped_lock<std::mutex> lock(gazebo_attachment_mutex_);
      gazebo_attached_block_pose_ = response->state.pose;
    }
    gazebo_attachment_warning_logged_ = false;

    const auto period = std::chrono::duration<double>(1.0 / std::max(1.0, gazebo_attach_update_hz_));
    gazebo_attachment_timer_ = create_wall_timer(
      std::chrono::duration_cast<std::chrono::nanoseconds>(period),
      std::bind(&ManipulationCommander::update_gazebo_attachment, this));

    RCLCPP_INFO(
      get_logger(),
      "Started Gazebo attachment for '%s' relative to '%s'",
      pickup_block_box_.id.c_str(), gazebo_attachment_frame_.c_str());
    return true;
  }

  void stop_gazebo_attachment()
  {
    if (gazebo_attachment_timer_) {
      gazebo_attachment_timer_->cancel();
      gazebo_attachment_timer_.reset();
      RCLCPP_INFO(get_logger(), "Stopped Gazebo attachment for '%s'", pickup_block_box_.id.c_str());
    }
  }

  void update_gazebo_attachment()
  {
    if (!pickup_block_attached_ || !gazebo_set_entity_state_client_) {
      return;
    }
    if (!gazebo_set_entity_state_client_->service_is_ready()) {
      return;
    }

    geometry_msgs::msg::Pose relative_pose;
    {
      std::scoped_lock<std::mutex> lock(gazebo_attachment_mutex_);
      relative_pose = gazebo_attached_block_pose_;
    }

    auto request = std::make_shared<SetEntityState::Request>();
    request->state.name = pickup_block_box_.id;
    request->state.reference_frame = gazebo_attachment_frame_;
    request->state.pose = relative_pose;
    request->state.twist.linear.x = 0.0;
    request->state.twist.linear.y = 0.0;
    request->state.twist.linear.z = 0.0;
    request->state.twist.angular.x = 0.0;
    request->state.twist.angular.y = 0.0;
    request->state.twist.angular.z = 0.0;

    gazebo_set_entity_state_client_->async_send_request(
      request,
      [this](rclcpp::Client<SetEntityState>::SharedFuture future) {
        const auto response = future.get();
        if (!response->success && !gazebo_attachment_warning_logged_) {
          gazebo_attachment_warning_logged_ = true;
          RCLCPP_WARN(get_logger(), "Gazebo attachment update failed for '%s'", pickup_block_box_.id.c_str());
        }
      });
  }

  bool ensure_current_state(std::string & error_message)
  {
    const auto current_state = arm_move_group_->getCurrentState(5.0);
    if (!current_state) {
      error_message = "Timed out waiting for current robot state";
      return false;
    }
    return true;
  }

  bool wait_for_execution_servers(
    const std::shared_ptr<GoalHandleExecuteTask> & goal_handle,
    ExecuteTask::Result & result,
    std::string & error_message)
  {
    if (check_cancel(goal_handle, result)) {
      error_message = "Task canceled";
      return false;
    }

    publish_feedback(goal_handle, Stage::IDLE, "Waiting for arm and gripper controllers");

    const auto deadline =
      std::chrono::steady_clock::now() + std::chrono::duration<double>(controller_ready_timeout_sec_);
    const auto arm_controller_name = controller_name_from_action(arm_controller_action_name_);
    const auto gripper_controller_name = controller_name_from_action(gripper_controller_action_name_);

    while (std::chrono::steady_clock::now() < deadline) {
      if (check_cancel(goal_handle, result)) {
        error_message = "Task canceled";
        return false;
      }

      if (!controller_manager_client_ ||
        !controller_manager_client_->wait_for_service(std::chrono::milliseconds(500)))
      {
        continue;
      }

      auto request = std::make_shared<ListControllers::Request>();
      auto future = controller_manager_client_->async_send_request(request);
      if (future.wait_for(std::chrono::seconds(10)) != std::future_status::ready) {
        continue;
      }

      const auto response = future.get();
      if (is_controller_active(response->controller, arm_controller_name) &&
        is_controller_active(response->controller, gripper_controller_name))
      {
        break;
      }
    }

    if (std::chrono::steady_clock::now() >= deadline) {
      error_message = "Arm or gripper controller did not become active in time";
      return false;
    }

    const auto action_timeout = std::chrono::seconds(5);
    if (!arm_controller_client_ || !arm_controller_client_->wait_for_action_server(action_timeout)) {
      error_message = "Arm controller action server is not ready";
      return false;
    }

    if (!gripper_controller_client_ || !gripper_controller_client_->wait_for_action_server(action_timeout)) {
      error_message = "Gripper controller action server is not ready";
      return false;
    }

    if (!ensure_current_state(error_message)) {
      return false;
    }

    return true;
  }

  bool check_cancel(
    const std::shared_ptr<GoalHandleExecuteTask> & goal_handle,
    ExecuteTask::Result & result)
  {
    if (!goal_handle) {
      return false;
    }

    if (!goal_handle->is_canceling()) {
      return false;
    }

    stop_motion();
    set_result(result, Stage::FAILED, ErrorCode::CANCELED, "Task canceled");
    return true;
  }

  void stop_motion()
  {
    std::scoped_lock<std::mutex> lock(move_group_mutex_);
    if (arm_move_group_) {
      arm_move_group_->stop();
    }
    if (gripper_move_group_) {
      gripper_move_group_->stop();
    }
  }

  void publish_feedback(
    const std::shared_ptr<GoalHandleExecuteTask> & goal_handle,
    Stage stage,
    const std::string & message)
  {
    if (!goal_handle) {
      RCLCPP_INFO(get_logger(), "[stage=%u] %s", static_cast<unsigned>(stage), message.c_str());
      return;
    }

    auto feedback = std::make_shared<ExecuteTask::Feedback>();
    feedback->current_stage = static_cast<uint8_t>(stage);
    feedback->message = message;
    goal_handle->publish_feedback(feedback);
  }

  void run_autostart_task()
  {
    if (!autostart_timer_) {
      return;
    }
    autostart_timer_->cancel();
    autostart_timer_.reset();

    if (busy_.exchange(true)) {
      return;
    }

    std::thread(&ManipulationCommander::execute_autostart_task, this).detach();
  }

  void execute_autostart_task()
  {

    ExecuteTask::Result result;
    result.success = false;
    result.stage_reached = static_cast<uint8_t>(Stage::IDLE);
    result.error_code = static_cast<int32_t>(ErrorCode::NONE);

    std::string error_message;
    if (!wait_for_execution_servers(nullptr, result, error_message)) {
      set_result(result, Stage::FAILED, ErrorCode::NOT_READY, error_message);
      RCLCPP_ERROR(
        get_logger(), "Autostart task failed at stage %u: %s",
        static_cast<unsigned>(result.stage_reached), result.message.c_str());
      busy_.store(false);
      return;
    }

    bool success = false;
    if (autostart_task_type_ == ExecuteTask::Goal::PICK_AND_PLACE_FIXED) {
      success = run_pick_and_place(nullptr, result, error_message);
    } else if (autostart_task_type_ == ExecuteTask::Goal::MOVE_HOME) {
      success = move_arm(nullptr, Stage::MOVING_HOME, home_target_, arm_execution_timeout_sec_, result, error_message);
    } else {
      set_result(result, Stage::FAILED, ErrorCode::INVALID_TASK, "Unsupported autostart task type");
    }

    if (success) {
      set_result(result, Stage::DONE, ErrorCode::NONE, "Autostart task completed successfully");
      RCLCPP_INFO(get_logger(), "Autostart task succeeded");
    } else {
      if (result.error_code == static_cast<int32_t>(ErrorCode::NONE)) {
        set_result(result, Stage::FAILED, ErrorCode::EXECUTION_FAILED, error_message);
      }
      RCLCPP_ERROR(
        get_logger(), "Autostart task failed at stage %u: %s",
        static_cast<unsigned>(result.stage_reached), result.message.c_str());
    }

    busy_.store(false);
  }

  void set_result(
    ExecuteTask::Result & result,
    Stage stage,
    ErrorCode error_code,
    const std::string & message)
  {
    result.success = (error_code == ErrorCode::NONE);
    result.stage_reached = stage_to_result(stage);
    result.error_code = static_cast<int32_t>(error_code);
    result.message = message;
  }

  uint8_t stage_to_result(Stage stage) const
  {
    return static_cast<uint8_t>(stage);
  }

  static std::string controller_name_from_action(const std::string & action_name)
  {
    const std::size_t separator = action_name.find('/');
    if (separator == std::string::npos) {
      return action_name;
    }
    return action_name.substr(0, separator);
  }

  static bool is_controller_active(
    const std::vector<controller_manager_msgs::msg::ControllerState> & controllers,
    const std::string & controller_name)
  {
    for (const auto & controller : controllers) {
      if (controller.name == controller_name) {
        return controller.state == "active";
      }
    }
    return false;
  }

  rclcpp_action::Server<ExecuteTask>::SharedPtr action_server_;
  rclcpp::Client<ListControllers>::SharedPtr controller_manager_client_;
  rclcpp::Client<GetEntityState>::SharedPtr gazebo_get_entity_state_client_;
  rclcpp::Client<SetEntityState>::SharedPtr gazebo_set_entity_state_client_;
  rclcpp_action::Client<control_msgs::action::FollowJointTrajectory>::SharedPtr arm_controller_client_;
  rclcpp_action::Client<control_msgs::action::FollowJointTrajectory>::SharedPtr gripper_controller_client_;
  std::unique_ptr<moveit::planning_interface::MoveGroupInterface> arm_move_group_;
  std::unique_ptr<moveit::planning_interface::MoveGroupInterface> gripper_move_group_;
  std::unique_ptr<moveit::planning_interface::PlanningSceneInterface> planning_scene_interface_;

  std::atomic_bool busy_{false};
  bool initialized_{false};
  bool enable_scene_objects_{true};
  bool enable_pickup_stand_collision_{false};
  bool enable_place_stand_collision_{true};
  bool enable_gazebo_attachment_{true};
  bool generate_pick_targets_from_block_{false};
  bool pickup_block_attached_{false};
  std::mutex move_group_mutex_;
  std::mutex gazebo_attachment_mutex_;

  std::string initialization_error_;
  std::string planning_frame_;
  std::string arm_group_name_;
  std::string gripper_group_name_;
  std::string arm_end_effector_link_;

  double arm_velocity_scaling_{0.2};
  double arm_acceleration_scaling_{0.2};
  double gripper_velocity_scaling_{0.8};
  double gripper_acceleration_scaling_{0.8};
  double arm_planning_time_sec_{5.0};
  double gripper_planning_time_sec_{3.0};
  double arm_execution_timeout_sec_{15.0};
  double gripper_execution_timeout_sec_{8.0};
  double controller_ready_timeout_sec_{30.0};
  double post_grasp_settle_sec_{0.7};
  double post_release_settle_sec_{0.4};
  double gazebo_attach_update_hz_{30.0};
  double gazebo_service_timeout_sec_{3.0};
  double gripper_open_joint7_{0.03};
  double gripper_close_joint7_{0.005};
  int64_t autostart_task_type_{0};
  std::string arm_controller_action_name_;
  std::string gripper_controller_action_name_;
  std::string gazebo_attachment_frame_{"gripper_base"};
  const std::vector<std::string> arm_joint_names_{"joint1", "joint2", "joint3", "joint4", "joint5", "joint6"};
  std::vector<std::string> attached_block_touch_links_;
  XYZ pick_target_orientation_rpy_{};
  std::vector<double> top_grasp_candidate_yaws_;
  XYZ pregrasp_offset_xyz_{};
  XYZ grasp_offset_xyz_{};
  XYZ lift_offset_xyz_{};
  XYZ transit_offset_xyz_{};
  XYZ tcp_offset_xyz_{};
  double grasp_candidate_planning_time_sec_{5.0};

  PoseTarget home_pose_{};
  PoseTarget pregrasp_pose_{};
  PoseTarget grasp_pose_{};
  PoseTarget lift_pose_{};
  PoseTarget place_pose_{};
  ArmTarget home_target_{};
  ArmTarget pregrasp_target_{};
  ArmTarget grasp_target_{};
  ArmTarget lift_target_{};
  ArmTarget transit_target_{};
  ArmTarget place_target_{};
  SceneBox pickup_stand_box_{};
  SceneBox place_stand_box_{};
  SceneBox pickup_block_box_{};
  rclcpp::TimerBase::SharedPtr autostart_timer_;
  rclcpp::TimerBase::SharedPtr gazebo_attachment_timer_;
  geometry_msgs::msg::Pose gazebo_attached_block_pose_{};
  bool gazebo_attachment_warning_logged_{false};

  friend int main(int argc, char ** argv);
};

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);

  auto node = std::make_shared<ManipulationCommander>();
  bool use_sim_time = false;
  node->get_parameter("use_sim_time", use_sim_time);
  node->set_parameter(rclcpp::Parameter("use_sim_time", use_sim_time));
  node->initialized_ = node->initialize();

  rclcpp::executors::MultiThreadedExecutor executor;
  executor.add_node(node);
  executor.spin();

  rclcpp::shutdown();
  return 0;
}
