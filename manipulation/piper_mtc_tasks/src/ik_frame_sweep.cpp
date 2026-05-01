#include <cmath>
#include <map>
#include <iomanip>
#include <iostream>
#include <limits>
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

struct Candidate
{
  double roll;
  double pitch;
  double yaw;
  double tcp_z;
  double grasp_angle;
  Eigen::VectorXd joints;
};

struct Box
{
  std::string id;
  Eigen::Vector3d center;
  Eigen::Vector3d size;
};

void add_box_to_scene(planning_scene::PlanningScene & scene, const Box & box)
{
  moveit_msgs::msg::CollisionObject object;
  object.header.frame_id = "base_link";
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

void add_pick_place_stand(
  planning_scene::PlanningScene & scene,
  const std::string & prefix,
  double x,
  double y)
{
  add_box_to_scene(
    scene,
    Box{
      prefix + "_tabletop",
      Eigen::Vector3d(x, y, 0.423),
      Eigen::Vector3d(0.22, 0.18, 0.02)});
  add_box_to_scene(
    scene,
    Box{
      prefix + "_pedestal",
      Eigen::Vector3d(x, y, 0.2015),
      Eigen::Vector3d(0.06, 0.06, 0.403)});
  add_box_to_scene(
    scene,
    Box{
      prefix + "_base",
      Eigen::Vector3d(x, y, 0.01),
      Eigen::Vector3d(0.12, 0.12, 0.02)});
}

Eigen::Matrix3d rpy_to_rotation(double roll, double pitch, double yaw)
{
  return (
    Eigen::AngleAxisd(yaw, Eigen::Vector3d::UnitZ()) *
    Eigen::AngleAxisd(pitch, Eigen::Vector3d::UnitY()) *
    Eigen::AngleAxisd(roll, Eigen::Vector3d::UnitX())).toRotationMatrix();
}

Eigen::Isometry3d make_transform(
  const Eigen::Vector3d & translation,
  double roll,
  double pitch,
  double yaw)
{
  Eigen::Isometry3d transform = Eigen::Isometry3d::Identity();
  transform.linear() = rpy_to_rotation(roll, pitch, yaw);
  transform.translation() = translation;
  return transform;
}

std::vector<double> range(double start, double stop, double step)
{
  std::vector<double> values;
  for (double value = start; value <= stop + 1e-9; value += step) {
    values.push_back(value);
  }
  return values;
}

std::vector<double> optional_range(
  const std::vector<double> & configured,
  double fallback)
{
  if (configured.empty()) {
    return {fallback};
  }
  if (configured.size() != 3) {
    throw std::runtime_error("Range parameter must contain exactly 3 elements.");
  }
  return range(configured[0], configured[1], configured[2]);
}

}  // namespace

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  auto node = std::make_shared<rclcpp::Node>("ik_frame_sweep");

  node->declare_parameter<std::string>("arm_group_name", "arm");
  node->declare_parameter<std::string>("hand_frame", "gripper_grasp_center");
  node->declare_parameter<bool>("check_table_collision", true);
  node->declare_parameter<double>("ik_timeout_sec", 0.05);
  node->declare_parameter<int>("max_results", 20);
  node->declare_parameter<std::vector<double>>("object_xyz", {0.281, 0.0, 0.4505});
  node->declare_parameter<double>("object_size_x", 0.045);
  node->declare_parameter<double>("object_size_y", 0.045);
  node->declare_parameter<double>("object_size_z", 0.035);
  node->declare_parameter<std::vector<double>>("tcp_z_range", {-0.04, 0.08, 0.005});
  node->declare_parameter<std::vector<double>>("tcp_xy", {0.0, 0.0});
  node->declare_parameter<std::vector<double>>("pregrasp_xyz", {0.0, 0.0, 0.0});
  node->declare_parameter<std::vector<double>>("target_x_range", std::vector<double>{});
  node->declare_parameter<std::vector<double>>("target_y_range", std::vector<double>{});
  node->declare_parameter<std::vector<double>>("target_z_range", std::vector<double>{});
  node->declare_parameter<std::vector<std::string>>("allowed_touch_links", std::vector<std::string>{});
  node->declare_parameter<std::vector<double>>(
    "roll_candidates", {-M_PI, -M_PI_2, 0.0, M_PI_2, M_PI});
  node->declare_parameter<std::vector<double>>(
    "pitch_candidates", {-M_PI_2, -M_PI / 4.0, 0.0, M_PI / 4.0, M_PI_2});
  node->declare_parameter<std::vector<double>>(
    "yaw_candidates", {-M_PI, -M_PI_2, 0.0, M_PI_2, M_PI});
  node->declare_parameter<std::vector<double>>("grasp_angles", {
    0.0, 0.261799387799, 0.523598775598, 0.785398163397,
    1.047197551197, 1.308996938996, 1.570796326795, 1.832595714594,
    2.094395102393, 2.356194490192, 2.617993877991, 2.879793265790,
    3.141592653590, 3.403392041389, 3.665191429188, 3.926990816987,
    4.188790204786, 4.450589592585, 4.712388980384, 4.974188368183,
    5.235987755982, 5.497787143781, 5.759586531580, 6.021385919379});

  const auto arm_group_name = node->get_parameter("arm_group_name").as_string();
  const auto hand_frame = node->get_parameter("hand_frame").as_string();
  const auto check_table_collision = node->get_parameter("check_table_collision").as_bool();
  const auto ik_timeout_sec = node->get_parameter("ik_timeout_sec").as_double();
  const auto max_results = node->get_parameter("max_results").as_int();
  const auto object_xyz_values = node->get_parameter("object_xyz").as_double_array();
  const auto object_size_x = node->get_parameter("object_size_x").as_double();
  const auto object_size_y = node->get_parameter("object_size_y").as_double();
  const auto object_size_z = node->get_parameter("object_size_z").as_double();
  const auto tcp_z_range_values = node->get_parameter("tcp_z_range").as_double_array();
  const auto tcp_xy_values = node->get_parameter("tcp_xy").as_double_array();
  const auto pregrasp_xyz_values = node->get_parameter("pregrasp_xyz").as_double_array();
  const auto target_x_range_values = node->get_parameter("target_x_range").as_double_array();
  const auto target_y_range_values = node->get_parameter("target_y_range").as_double_array();
  const auto target_z_range_values = node->get_parameter("target_z_range").as_double_array();
  const auto allowed_touch_links = node->get_parameter("allowed_touch_links").as_string_array();
  const auto roll_candidates = node->get_parameter("roll_candidates").as_double_array();
  const auto pitch_candidates = node->get_parameter("pitch_candidates").as_double_array();
  const auto yaw_candidates = node->get_parameter("yaw_candidates").as_double_array();
  const auto grasp_angles = node->get_parameter("grasp_angles").as_double_array();

  if (
    object_xyz_values.size() != 3 || tcp_z_range_values.size() != 3 ||
    tcp_xy_values.size() != 2 || pregrasp_xyz_values.size() != 3)
  {
    RCLCPP_ERROR(
      node->get_logger(),
      "object_xyz, tcp_z_range, tcp_xy, and pregrasp_xyz have invalid sizes");
    rclcpp::shutdown();
    return 2;
  }

  robot_model_loader::RobotModelLoader loader(node, "robot_description");
  const auto robot_model = loader.getModel();
  if (!robot_model) {
    RCLCPP_ERROR(node->get_logger(), "Failed to load robot model");
    rclcpp::shutdown();
    return 2;
  }

  const auto * joint_model_group = robot_model->getJointModelGroup(arm_group_name);
  if (joint_model_group == nullptr) {
    RCLCPP_ERROR(node->get_logger(), "Joint model group '%s' was not found", arm_group_name.c_str());
    rclcpp::shutdown();
    return 2;
  }

  Eigen::Isometry3d object_pose = Eigen::Isometry3d::Identity();
  object_pose.translation() = Eigen::Vector3d(
    object_xyz_values[0],
    object_xyz_values[1],
    object_xyz_values[2]);

  const auto tcp_z_values =
    range(tcp_z_range_values[0], tcp_z_range_values[1], tcp_z_range_values[2]);
  const auto target_x_values = optional_range(target_x_range_values, pregrasp_xyz_values[0]);
  const auto target_y_values = optional_range(target_y_range_values, pregrasp_xyz_values[1]);
  const auto target_z_values = optional_range(target_z_range_values, pregrasp_xyz_values[2]);

  planning_scene::PlanningScene scene(robot_model);
  if (check_table_collision) {
    add_pick_place_stand(scene, "pickup_stand_box", 0.281, 0.0);
    add_pick_place_stand(scene, "place_stand_box", -0.02, 0.38);
  }
  add_box_to_scene(
    scene,
    Box{
      "pick_target_block",
      Eigen::Vector3d(object_xyz_values[0], object_xyz_values[1], object_xyz_values[2]),
      Eigen::Vector3d(object_size_x, object_size_y, object_size_z)});
  auto & acm = scene.getAllowedCollisionMatrixNonConst();
  for (const auto & link_name : allowed_touch_links) {
    acm.setEntry("pick_target_block", link_name, true);
  }

  moveit::core::RobotState seed_state(robot_model);
  seed_state.setToDefaultValues();

  std::vector<Candidate> successes;
  std::map<std::string, int> rejected_contacts;
  int ik_failures = 0;
  int collision_rejections = 0;

  for (const double roll : roll_candidates) {
    for (const double pitch : pitch_candidates) {
      for (const double yaw : yaw_candidates) {
        for (const double target_x : target_x_values) {
          for (const double target_y : target_y_values) {
            for (const double target_z : target_z_values) {
              for (const double tcp_z : tcp_z_values) {
                Eigen::Isometry3d ik_frame = make_transform(
                  Eigen::Vector3d(
                    target_x - tcp_xy_values[0],
                    target_y - tcp_xy_values[1],
                    object_size_z * 0.5 + target_z - tcp_z),
                  roll,
                  pitch,
                  yaw);

                for (const double grasp_angle : grasp_angles) {
                  Eigen::Isometry3d target_pose = object_pose;
                  target_pose.linear() =
                    (Eigen::AngleAxisd(grasp_angle, Eigen::Vector3d::UnitZ())).toRotationMatrix();
                  const Eigen::Isometry3d hand_target = target_pose * ik_frame.inverse();

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

                  if (check_table_collision) {
                    state.update();
                    collision_detection::CollisionRequest request;
                    collision_detection::CollisionResult result;
                    request.contacts = true;
                    request.max_contacts = 20;
                    request.max_contacts_per_pair = 3;
                    scene.checkCollision(request, result, state);
                    if (result.collision) {
                      ++collision_rejections;
                      for (const auto & contact : result.contacts) {
                        ++rejected_contacts[contact.first.first + " <-> " + contact.first.second];
                      }
                      continue;
                    }
                  }

                  Eigen::VectorXd joint_values;
                  state.copyJointGroupPositions(joint_model_group, joint_values);
                  successes.push_back(Candidate{roll, pitch, yaw, tcp_z, grasp_angle, joint_values});
                  if (static_cast<int>(successes.size()) >= max_results) {
                    break;
                  }
                }
                if (static_cast<int>(successes.size()) >= max_results) {
                  break;
                }
              }
              if (static_cast<int>(successes.size()) >= max_results) {
                break;
              }
            }
            if (static_cast<int>(successes.size()) >= max_results) {
              break;
            }
          }
          if (static_cast<int>(successes.size()) >= max_results) {
            break;
          }
        }
        if (static_cast<int>(successes.size()) >= max_results) {
          break;
        }
      }
      if (static_cast<int>(successes.size()) >= max_results) {
        break;
      }
    }
    if (static_cast<int>(successes.size()) >= max_results) {
      break;
    }
  }

  if (successes.empty()) {
    RCLCPP_ERROR(
      node->get_logger(),
      "No valid candidates found. ik_failures=%d collision_rejections=%d",
      ik_failures,
      collision_rejections);
    for (const auto & contact : rejected_contacts) {
      RCLCPP_ERROR(
        node->get_logger(),
        "Rejected contact pair: %s count=%d",
        contact.first.c_str(),
        contact.second);
    }
    rclcpp::shutdown();
    return 1;
  }

  RCLCPP_INFO(
    node->get_logger(),
    "Found %zu valid candidates. ik_failures=%d collision_rejections=%d",
    successes.size(),
    ik_failures,
    collision_rejections);
  std::cout << std::fixed << std::setprecision(6);
  for (std::size_t i = 0; i < successes.size(); ++i) {
    const auto & candidate = successes[i];
    std::cout
      << "candidate " << i
      << " grasp_orientation_rpy=[" << candidate.roll << ", "
      << candidate.pitch << ", " << candidate.yaw << "]"
      << " tcp_offset_xyz=[0, 0, " << candidate.tcp_z << "]"
      << " grasp_angle=" << candidate.grasp_angle
      << " joints=[";
    for (Eigen::Index joint_index = 0; joint_index < candidate.joints.size(); ++joint_index) {
      if (joint_index > 0) {
        std::cout << ", ";
      }
      std::cout << candidate.joints[joint_index];
    }
    std::cout << "]\n";
  }

  rclcpp::shutdown();
  return 0;
}
