#include <cmath>
#include <iomanip>
#include <iostream>
#include <string>
#include <vector>

#include <Eigen/Geometry>
#include <geometry_msgs/msg/pose.hpp>
#include <moveit/planning_scene/planning_scene.h>
#include <moveit/robot_model_loader/robot_model_loader.h>
#include <moveit/robot_state/robot_state.h>
#include <moveit_msgs/msg/collision_object.hpp>
#include <rclcpp/rclcpp.hpp>
#include <shape_msgs/msg/solid_primitive.hpp>

namespace
{

struct Box
{
  std::string id;
  Eigen::Vector3d center;
  Eigen::Vector3d size;
};

struct PoseCase
{
  std::string name;
  Eigen::Vector3d position;
  std::vector<Eigen::Vector3d> rpy_candidates;
};

struct ProbeResult
{
  std::string name;
  bool ok{false};
  bool ik_solved{false};
  bool in_bounds{false};
  bool collision_free{false};
  std::string reason;
  Eigen::Vector3d rpy{0.0, 0.0, 0.0};
  Eigen::VectorXd joints;
};

Eigen::Matrix3d rpy_to_rotation(double roll, double pitch, double yaw)
{
  return (
    Eigen::AngleAxisd(yaw, Eigen::Vector3d::UnitZ()) *
    Eigen::AngleAxisd(pitch, Eigen::Vector3d::UnitY()) *
    Eigen::AngleAxisd(roll, Eigen::Vector3d::UnitX())).toRotationMatrix();
}

Eigen::Isometry3d make_pose(const Eigen::Vector3d & xyz, const Eigen::Vector3d & rpy)
{
  Eigen::Isometry3d pose = Eigen::Isometry3d::Identity();
  pose.translation() = xyz;
  pose.linear() = rpy_to_rotation(rpy.x(), rpy.y(), rpy.z());
  return pose;
}

void add_box_to_scene(
  planning_scene::PlanningScene & scene,
  const std::string & frame_id,
  const Box & box)
{
  moveit_msgs::msg::CollisionObject object;
  object.header.frame_id = frame_id;
  object.id = box.id;
  object.operation = moveit_msgs::msg::CollisionObject::ADD;

  shape_msgs::msg::SolidPrimitive primitive;
  primitive.type = shape_msgs::msg::SolidPrimitive::BOX;
  primitive.dimensions = {box.size.x(), box.size.y(), box.size.z()};
  object.primitives.push_back(primitive);

  geometry_msgs::msg::Pose pose;
  pose.position.x = box.center.x();
  pose.position.y = box.center.y();
  pose.position.z = box.center.z();
  pose.orientation.w = 1.0;
  object.primitive_poses.push_back(pose);

  scene.processCollisionObjectMsg(object);
}

bool read_xyz(const rclcpp::Node & node, const std::string & name, Eigen::Vector3d & output)
{
  const auto values = node.get_parameter(name).as_double_array();
  if (values.size() != 3) {
    return false;
  }
  output = Eigen::Vector3d(values[0], values[1], values[2]);
  return true;
}

std::vector<Eigen::Vector3d> read_xyz_list(
  const rclcpp::Node & node,
  const std::string & name)
{
  const auto values = node.get_parameter(name).as_double_array();
  if (values.empty()) {
    return {};
  }
  if (values.size() % 3 != 0) {
    throw std::runtime_error("Parameter '" + name + "' must contain xyz triples.");
  }

  std::vector<Eigen::Vector3d> points;
  for (std::size_t i = 0; i < values.size(); i += 3) {
    points.emplace_back(values[i], values[i + 1], values[i + 2]);
  }
  return points;
}

std::vector<double> read_candidates_or_default(
  const rclcpp::Node & node,
  const std::string & name,
  double fallback)
{
  const auto values = node.get_parameter(name).as_double_array();
  if (values.empty()) {
    return {fallback};
  }
  return std::vector<double>(values.begin(), values.end());
}

std::vector<Eigen::Vector3d> make_rpy_candidates(
  const std::vector<double> & rolls,
  const std::vector<double> & pitches,
  const std::vector<double> & yaws)
{
  std::vector<Eigen::Vector3d> candidates;
  candidates.reserve(rolls.size() * pitches.size() * yaws.size());
  for (const double roll : rolls) {
    for (const double pitch : pitches) {
      for (const double yaw : yaws) {
        candidates.emplace_back(roll, pitch, yaw);
      }
    }
  }
  return candidates;
}

std::vector<std::string> default_slot_names(std::size_t count)
{
  std::vector<std::string> names;
  names.reserve(count);
  for (std::size_t i = 0; i < count; ++i) {
    if (i == 0) {
      names.push_back("near_white_slot");
    } else if (i == 1) {
      names.push_back("far_black_slot");
    } else {
      names.push_back("slot_" + std::to_string(i));
    }
  }
  return names;
}

ProbeResult check_pose(
  const PoseCase & pose_case,
  const moveit::core::RobotModelConstPtr & robot_model,
  const moveit::core::JointModelGroup * joint_model_group,
  planning_scene::PlanningScene & scene,
  const std::string & hand_frame,
  double ik_timeout_sec,
  bool check_collisions)
{
  ProbeResult result;
  result.name = pose_case.name;

  int ik_failures = 0;
  int bound_failures = 0;
  int collision_failures = 0;
  std::string first_collision;

  for (const auto & rpy : pose_case.rpy_candidates) {
    moveit::core::RobotState state(robot_model);
    state.setToDefaultValues();
    const bool solved = state.setFromIK(
      joint_model_group,
      make_pose(pose_case.position, rpy),
      hand_frame,
      ik_timeout_sec);
    if (!solved) {
      ++ik_failures;
      continue;
    }
    result.ik_solved = true;

    state.update();
    if (!state.satisfiesBounds(joint_model_group)) {
      ++bound_failures;
      state.copyJointGroupPositions(joint_model_group, result.joints);
      continue;
    }
    result.in_bounds = true;

    if (check_collisions) {
      collision_detection::CollisionRequest request;
      collision_detection::CollisionResult collision_result;
      request.contacts = true;
      request.max_contacts = 10;
      request.max_contacts_per_pair = 2;
      scene.checkCollision(request, collision_result, state);
      if (collision_result.collision) {
        ++collision_failures;
        if (first_collision.empty()) {
          for (const auto & contact : collision_result.contacts) {
            first_collision = contact.first.first + "<->" + contact.first.second;
            break;
          }
        }
        state.copyJointGroupPositions(joint_model_group, result.joints);
        continue;
      }
    }

    result.collision_free = true;
    result.ok = true;
    result.reason = "ok";
    result.rpy = rpy;
    state.copyJointGroupPositions(joint_model_group, result.joints);
    return result;
  }

  if (!result.ik_solved) {
    result.reason = "IK failed for all " + std::to_string(ik_failures) + " orientations";
  } else if (!result.in_bounds) {
    result.reason =
      "all IK solutions violate bounds; ik_failures=" + std::to_string(ik_failures) +
      " bound_failures=" + std::to_string(bound_failures);
  } else {
    result.reason =
      "all IK solutions collide; ik_failures=" + std::to_string(ik_failures) +
      " bound_failures=" + std::to_string(bound_failures) +
      " collision_failures=" + std::to_string(collision_failures);
    if (!first_collision.empty()) {
      result.reason += " first_collision=" + first_collision;
    }
  }
  return result;
}

ProbeResult check_joint_posture(
  const std::string & name,
  const std::vector<double> & joint_values,
  const moveit::core::RobotModelConstPtr & robot_model,
  const moveit::core::JointModelGroup * joint_model_group,
  planning_scene::PlanningScene & scene,
  bool check_collisions)
{
  ProbeResult result;
  result.name = name;
  result.ik_solved = true;

  moveit::core::RobotState state(robot_model);
  state.setToDefaultValues();
  if (joint_values.size() != joint_model_group->getVariableCount()) {
    result.reason =
      "joint vector length " + std::to_string(joint_values.size()) +
      " does not match group variable count " +
      std::to_string(joint_model_group->getVariableCount());
    return result;
  }

  state.setJointGroupPositions(joint_model_group, joint_values);
  state.update();
  result.in_bounds = state.satisfiesBounds(joint_model_group);
  state.copyJointGroupPositions(joint_model_group, result.joints);
  if (!result.in_bounds) {
    result.reason = "joint posture violates bounds";
    return result;
  }

  if (check_collisions) {
    collision_detection::CollisionRequest request;
    collision_detection::CollisionResult collision_result;
    request.contacts = true;
    request.max_contacts = 10;
    request.max_contacts_per_pair = 2;
    scene.checkCollision(request, collision_result, state);
    result.collision_free = !collision_result.collision;
    if (collision_result.collision) {
      result.reason = "collision";
      for (const auto & contact : collision_result.contacts) {
        result.reason += " " + contact.first.first + "<->" + contact.first.second;
        break;
      }
      return result;
    }
  } else {
    result.collision_free = true;
  }

  result.ok = true;
  result.reason = "ok";
  return result;
}

void print_result(const ProbeResult & result)
{
  std::cout << (result.ok ? "OK  " : "FAIL") << " " << result.name
            << " ik=" << (result.ik_solved ? "yes" : "no")
            << " bounds=" << (result.in_bounds ? "yes" : "no")
            << " collision_free=" << (result.collision_free ? "yes" : "no")
            << " rpy=[" << result.rpy.x() << ", " << result.rpy.y() << ", " << result.rpy.z() << "]"
            << " reason=" << result.reason
            << " joints=[";
  for (Eigen::Index i = 0; i < result.joints.size(); ++i) {
    if (i > 0) {
      std::cout << ", ";
    }
    std::cout << result.joints[i];
  }
  std::cout << "]\n";
}

}  // namespace

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  auto node = std::make_shared<rclcpp::Node>("task_pose_reachability_probe");

  node->declare_parameter<std::string>("planning_frame", "piper_base_link");
  node->declare_parameter<std::string>("arm_group_name", "arm");
  node->declare_parameter<std::string>("hand_frame", "piper_gripper_grasp_center");
  node->declare_parameter<double>("ik_timeout_sec", 0.08);
  node->declare_parameter<bool>("check_collisions", true);
  node->declare_parameter<bool>("add_pickup_table_collision", true);
  node->declare_parameter<std::vector<double>>(
    "initial_joint_posture", {0.0, 0.95, -1.45, 0.0, 0.55, 0.0});
  node->declare_parameter<std::vector<double>>("observe_pose.xyz", {0.18, 0.0, 0.42});
  node->declare_parameter<std::vector<double>>("observe_pose.rpy", {3.14159, 0.0, 0.0});
  node->declare_parameter<std::vector<double>>("grasp_orientation_rpy", {0.0, -1.57079632679, 0.0});
  node->declare_parameter<std::vector<double>>("grasp_roll_candidates", std::vector<double>{});
  node->declare_parameter<std::vector<double>>("grasp_pitch_candidates", std::vector<double>{});
  node->declare_parameter<std::vector<double>>("grasp_yaw_candidates", std::vector<double>{});
  node->declare_parameter<std::vector<double>>("pregrasp_offset_xyz", {0.0, 0.0, 0.07});
  node->declare_parameter<std::vector<double>>("lift_offset_xyz", {0.0, 0.0, 0.06});
  node->declare_parameter<std::vector<double>>(
    "platform_slots_xyz", {0.0, 0.20, 0.30, 0.0, 0.28, 0.30});
  node->declare_parameter<std::vector<std::string>>(
    "platform_slot_names", std::vector<std::string>{});
  node->declare_parameter<std::vector<double>>("sample_box_release_xyz", std::vector<double>{});
  node->declare_parameter<std::vector<double>>("box_release_offset_xyz", {0.0, 0.0, 0.10});
  node->declare_parameter<std::string>("pickup_table.id", "payload_platform");
  node->declare_parameter<std::vector<double>>("pickup_table.center_xyz", {0.0, 0.24, 0.14});
  node->declare_parameter<std::vector<double>>("pickup_table.size_xyz", {0.18, 0.18, 0.02});

  const auto planning_frame = node->get_parameter("planning_frame").as_string();
  const auto arm_group_name = node->get_parameter("arm_group_name").as_string();
  const auto hand_frame = node->get_parameter("hand_frame").as_string();
  const auto ik_timeout_sec = node->get_parameter("ik_timeout_sec").as_double();
  const auto check_collisions = node->get_parameter("check_collisions").as_bool();
  const auto add_pickup_table_collision =
    node->get_parameter("add_pickup_table_collision").as_bool();
  const auto initial_joint_posture =
    node->get_parameter("initial_joint_posture").as_double_array();
  const auto slot_names_param =
    node->get_parameter("platform_slot_names").as_string_array();

  Eigen::Vector3d observe_xyz;
  Eigen::Vector3d observe_rpy;
  Eigen::Vector3d grasp_rpy;
  Eigen::Vector3d pregrasp_offset;
  Eigen::Vector3d lift_offset;
  Eigen::Vector3d box_release_offset;
  Eigen::Vector3d table_center;
  Eigen::Vector3d table_size;
  if (!read_xyz(*node, "observe_pose.xyz", observe_xyz) ||
    !read_xyz(*node, "observe_pose.rpy", observe_rpy) ||
    !read_xyz(*node, "grasp_orientation_rpy", grasp_rpy) ||
    !read_xyz(*node, "pregrasp_offset_xyz", pregrasp_offset) ||
    !read_xyz(*node, "lift_offset_xyz", lift_offset) ||
    !read_xyz(*node, "box_release_offset_xyz", box_release_offset) ||
    !read_xyz(*node, "pickup_table.center_xyz", table_center) ||
    !read_xyz(*node, "pickup_table.size_xyz", table_size))
  {
    RCLCPP_ERROR(node->get_logger(), "One or more xyz/rpy parameters do not have exactly 3 values.");
    rclcpp::shutdown();
    return 2;
  }

  const auto slots = read_xyz_list(*node, "platform_slots_xyz");
  const auto sample_box_releases = read_xyz_list(*node, "sample_box_release_xyz");
  const auto grasp_rpy_candidates = make_rpy_candidates(
    read_candidates_or_default(*node, "grasp_roll_candidates", grasp_rpy.x()),
    read_candidates_or_default(*node, "grasp_pitch_candidates", grasp_rpy.y()),
    read_candidates_or_default(*node, "grasp_yaw_candidates", grasp_rpy.z()));
  auto slot_names = slot_names_param.empty() ? default_slot_names(slots.size()) : slot_names_param;
  if (slot_names.size() != slots.size()) {
    RCLCPP_ERROR(
      node->get_logger(),
      "platform_slot_names must be empty or have the same length as platform_slots_xyz.");
    rclcpp::shutdown();
    return 2;
  }

  robot_model_loader::RobotModelLoader loader(node, "robot_description");
  const auto robot_model = loader.getModel();
  if (!robot_model) {
    RCLCPP_ERROR(node->get_logger(), "Failed to load robot model.");
    rclcpp::shutdown();
    return 2;
  }

  const auto * joint_model_group = robot_model->getJointModelGroup(arm_group_name);
  if (joint_model_group == nullptr) {
    RCLCPP_ERROR(node->get_logger(), "Joint model group '%s' was not found.", arm_group_name.c_str());
    rclcpp::shutdown();
    return 2;
  }

  planning_scene::PlanningScene scene(robot_model);
  if (add_pickup_table_collision) {
    add_box_to_scene(
      scene,
      planning_frame,
      Box{node->get_parameter("pickup_table.id").as_string(), table_center, table_size});
  }

  std::vector<ProbeResult> results;
  results.push_back(
    check_joint_posture(
      "shared_initial_joint_posture",
      initial_joint_posture,
      robot_model,
      joint_model_group,
      scene,
      check_collisions));

  std::vector<PoseCase> pose_cases;
  pose_cases.push_back(PoseCase{"observe_tcp_pose", observe_xyz, {observe_rpy}});

  for (std::size_t i = 0; i < slots.size(); ++i) {
    const auto & slot = slots[i];
    const auto & name = slot_names[i];
    pose_cases.push_back(PoseCase{name + "_pregrasp", slot + pregrasp_offset, grasp_rpy_candidates});
    pose_cases.push_back(PoseCase{name + "_grasp", slot, grasp_rpy_candidates});
    pose_cases.push_back(PoseCase{name + "_lift", slot + lift_offset, grasp_rpy_candidates});
    pose_cases.push_back(PoseCase{name + "_release_retreat", slot + box_release_offset, grasp_rpy_candidates});
  }

  for (std::size_t i = 0; i < sample_box_releases.size(); ++i) {
    pose_cases.push_back(
      PoseCase{
        "sample_box_" + std::to_string(i) + "_release",
        sample_box_releases[i] + box_release_offset,
        grasp_rpy_candidates});
  }

  for (const auto & pose_case : pose_cases) {
    results.push_back(
      check_pose(
        pose_case,
        robot_model,
        joint_model_group,
        scene,
        hand_frame,
        ik_timeout_sec,
        check_collisions));
  }

  std::cout << std::fixed << std::setprecision(6);
  int failures = 0;
  for (const auto & result : results) {
    print_result(result);
    if (!result.ok) {
      ++failures;
    }
  }

  RCLCPP_INFO(
    node->get_logger(),
    "Reachability probe finished: %zu cases, %d failures.",
    results.size(),
    failures);

  rclcpp::shutdown();
  return failures == 0 ? 0 : 1;
}
