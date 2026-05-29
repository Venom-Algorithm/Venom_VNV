#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>
#include <string>
#include <vector>

#include <Eigen/Geometry>
#include <moveit/planning_scene/planning_scene.h>
#include <moveit/robot_model_loader/robot_model_loader.h>
#include <moveit/robot_state/robot_state.h>
#include <rclcpp/rclcpp.hpp>

namespace
{

struct Candidate
{
  double x{};
  double y{};
  double z{};
  int solved_orientations{};
  double best_joint_distance{};
  Eigen::VectorXd best_joints;
};

Eigen::Matrix3d rpy_to_rotation(double roll, double pitch, double yaw)
{
  return (
    Eigen::AngleAxisd(yaw, Eigen::Vector3d::UnitZ()) *
    Eigen::AngleAxisd(pitch, Eigen::Vector3d::UnitY()) *
    Eigen::AngleAxisd(roll, Eigen::Vector3d::UnitX())).toRotationMatrix();
}

std::vector<double> range(double start, double stop, double step)
{
  std::vector<double> values;
  if (step <= 0.0) {
    throw std::runtime_error("Range step must be positive.");
  }
  for (double value = start; value <= stop + 1e-9; value += step) {
    values.push_back(value);
  }
  return values;
}

double joint_distance_from_zero(
  const moveit::core::RobotState & state,
  const moveit::core::JointModelGroup * joint_model_group)
{
  Eigen::VectorXd joints;
  state.copyJointGroupPositions(joint_model_group, joints);
  double sum_sq = 0.0;
  for (Eigen::Index i = 0; i < joints.size(); ++i) {
    sum_sq += joints[i] * joints[i];
  }
  return std::sqrt(sum_sq);
}

double score_candidate(const Candidate & candidate)
{
  // Lower is better. Keep the payload close to zero/home posture and near centerline.
  return candidate.best_joint_distance + 0.8 * std::abs(candidate.y) - 0.08 * candidate.solved_orientations;
}

}  // namespace

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  auto node = std::make_shared<rclcpp::Node>("payload_mount_sweep");

  node->declare_parameter<std::string>("arm_group_name", "arm");
  node->declare_parameter<std::string>("hand_frame", "piper_gripper_grasp_center");
  node->declare_parameter<double>("ik_timeout_sec", 0.03);
  node->declare_parameter<int>("max_results", 30);
  node->declare_parameter<std::vector<double>>("target_x_range", {0.12, 0.40, 0.02});
  node->declare_parameter<std::vector<double>>("target_y_range", {-0.24, 0.24, 0.02});
  node->declare_parameter<std::vector<double>>("target_z_range", {0.06, 0.20, 0.02});
  node->declare_parameter<std::vector<double>>("roll_candidates", {0.0});
  node->declare_parameter<std::vector<double>>("pitch_candidates", {-1.57079632679});
  node->declare_parameter<std::vector<double>>(
    "yaw_candidates", {-1.57079632679, -0.78539816339, 0.0, 0.78539816339, 1.57079632679});

  const auto arm_group_name = node->get_parameter("arm_group_name").as_string();
  const auto hand_frame = node->get_parameter("hand_frame").as_string();
  const auto ik_timeout_sec = node->get_parameter("ik_timeout_sec").as_double();
  const auto max_results = node->get_parameter("max_results").as_int();
  const auto x_range_param = node->get_parameter("target_x_range").as_double_array();
  const auto y_range_param = node->get_parameter("target_y_range").as_double_array();
  const auto z_range_param = node->get_parameter("target_z_range").as_double_array();
  const auto roll_candidates = node->get_parameter("roll_candidates").as_double_array();
  const auto pitch_candidates = node->get_parameter("pitch_candidates").as_double_array();
  const auto yaw_candidates = node->get_parameter("yaw_candidates").as_double_array();

  if (x_range_param.size() != 3 || y_range_param.size() != 3 || z_range_param.size() != 3) {
    RCLCPP_ERROR(node->get_logger(), "target_*_range parameters must be [start, stop, step].");
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

  moveit::core::RobotState seed_state(robot_model);
  seed_state.setToDefaultValues();
  if (robot_model->hasJointModelGroup(arm_group_name)) {
    seed_state.setToDefaultValues(joint_model_group, "zero");
  }
  seed_state.update();
  const Eigen::Isometry3d & zero_hand_pose = seed_state.getGlobalLinkTransform(hand_frame);
  const Eigen::Vector3d zero_rpy = zero_hand_pose.linear().eulerAngles(0, 1, 2);
  RCLCPP_INFO(
    node->get_logger(),
    "Zero hand pose in planning frame: xyz=[%.4f, %.4f, %.4f], rpy=[%.4f, %.4f, %.4f]",
    zero_hand_pose.translation().x(),
    zero_hand_pose.translation().y(),
    zero_hand_pose.translation().z(),
    zero_rpy.x(),
    zero_rpy.y(),
    zero_rpy.z());

  const auto x_values = range(x_range_param[0], x_range_param[1], x_range_param[2]);
  const auto y_values = range(y_range_param[0], y_range_param[1], y_range_param[2]);
  const auto z_values = range(z_range_param[0], z_range_param[1], z_range_param[2]);

  std::vector<Candidate> candidates;
  int ik_failures = 0;

  for (const double x : x_values) {
    for (const double y : y_values) {
      for (const double z : z_values) {
        Candidate candidate;
        candidate.x = x;
        candidate.y = y;
        candidate.z = z;
        candidate.best_joint_distance = std::numeric_limits<double>::infinity();

        for (const double roll : roll_candidates) {
          for (const double pitch : pitch_candidates) {
            for (const double yaw : yaw_candidates) {
              Eigen::Isometry3d hand_target = Eigen::Isometry3d::Identity();
              hand_target.translation() = Eigen::Vector3d(x, y, z);
              hand_target.linear() = rpy_to_rotation(roll, pitch, yaw);

              moveit::core::RobotState state(seed_state);
              const bool solved = state.setFromIK(
                joint_model_group,
                hand_target,
                hand_frame,
                ik_timeout_sec);
              if (!solved) {
                ++ik_failures;
                continue;
              }

              const double joint_distance = joint_distance_from_zero(state, joint_model_group);
              ++candidate.solved_orientations;
              if (joint_distance < candidate.best_joint_distance) {
                candidate.best_joint_distance = joint_distance;
                state.copyJointGroupPositions(joint_model_group, candidate.best_joints);
              }
            }
          }
        }

        if (candidate.solved_orientations > 0) {
          candidates.push_back(candidate);
        }
      }
    }
  }

  std::sort(
    candidates.begin(),
    candidates.end(),
    [](const Candidate & lhs, const Candidate & rhs) {
      return score_candidate(lhs) < score_candidate(rhs);
    });

  RCLCPP_INFO(
    node->get_logger(),
    "Scanned %zu points, found %zu reachable points, ik_failures=%d",
    x_values.size() * y_values.size() * z_values.size(),
    candidates.size(),
    ik_failures);

  const int count = std::min<int>(max_results, candidates.size());
  std::cout << std::fixed << std::setprecision(4);
  std::cout << "rank,x,y,z,solved_orientations,joint_distance,joints\n";
  for (int i = 0; i < count; ++i) {
    const auto & candidate = candidates[static_cast<std::size_t>(i)];
    std::cout
      << i << ","
      << candidate.x << ","
      << candidate.y << ","
      << candidate.z << ","
      << candidate.solved_orientations << ","
      << candidate.best_joint_distance << ",[";
    for (Eigen::Index joint_index = 0; joint_index < candidate.best_joints.size(); ++joint_index) {
      if (joint_index > 0) {
        std::cout << " ";
      }
      std::cout << candidate.best_joints[joint_index];
    }
    std::cout << "]\n";
  }

  rclcpp::shutdown();
  return candidates.empty() ? 1 : 0;
}
