#include <array>
#include <chrono>
#include <cmath>
#include <optional>
#include <sstream>
#include <string>
#include <utility>

#include "diagnostic_msgs/msg/diagnostic_array.hpp"
#include "diagnostic_msgs/msg/diagnostic_status.hpp"
#include "diagnostic_msgs/msg/key_value.hpp"
#include "nav_msgs/msg/odometry.hpp"
#include "px4_msgs/msg/battery_status.hpp"
#include "px4_msgs/msg/failsafe_flags.hpp"
#include "px4_msgs/msg/timesync_status.hpp"
#include "px4_msgs/msg/vehicle_control_mode.hpp"
#include "px4_msgs/msg/vehicle_odometry.hpp"
#include "px4_msgs/msg/vehicle_status.hpp"
#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"
#include "venom_px4_bridge/frame_conversions.hpp"
#include "venom_px4_bridge/px4_bridge_types.hpp"
#include "venom_px4_bridge/px4_vehicle_state.hpp"

namespace venom_px4_bridge
{

namespace
{

rclcpp::QoS px4_qos()
{
  auto qos = rclcpp::QoS(rclcpp::KeepLast(10));
  qos.best_effort();
  qos.durability_volatile();
  return qos;
}

std::string join_topic(const std::string & prefix, const std::string & suffix)
{
  if (prefix.empty()) {
    return suffix;
  }

  if (prefix.back() == '/') {
    return prefix.substr(0, prefix.size() - 1) + suffix;
  }

  return prefix + suffix;
}

diagnostic_msgs::msg::KeyValue key_value(std::string key, std::string value)
{
  diagnostic_msgs::msg::KeyValue item;
  item.key = std::move(key);
  item.value = std::move(value);
  return item;
}

template<typename ArrayT>
void set_pose_covariance(double * covariance, const ArrayT & position_var, const ArrayT & orientation_var)
{
  covariance[0] = std::isfinite(position_var[0]) ? position_var[1] : -1.0;
  covariance[7] = std::isfinite(position_var[1]) ? position_var[0] : -1.0;
  covariance[14] = std::isfinite(position_var[2]) ? position_var[2] : -1.0;
  covariance[21] = std::isfinite(orientation_var[0]) ? orientation_var[0] : -1.0;
  covariance[28] = std::isfinite(orientation_var[1]) ? orientation_var[1] : -1.0;
  covariance[35] = std::isfinite(orientation_var[2]) ? orientation_var[2] : -1.0;
}

template<typename ArrayT>
void set_twist_covariance(double * covariance, const ArrayT & velocity_var)
{
  covariance[0] = std::isfinite(velocity_var[0]) ? velocity_var[1] : -1.0;
  covariance[7] = std::isfinite(velocity_var[1]) ? velocity_var[0] : -1.0;
  covariance[14] = std::isfinite(velocity_var[2]) ? velocity_var[2] : -1.0;
  covariance[21] = -1.0;
  covariance[28] = -1.0;
  covariance[35] = -1.0;
}

}  // namespace

class Px4StatusAdapter : public rclcpp::Node
{
public:
  Px4StatusAdapter()
  : Node("px4_status_adapter")
  {
    const auto fmu_prefix = this->declare_parameter<std::string>("fmu_prefix", "/fmu");
    const auto bridge_prefix = this->declare_parameter<std::string>("bridge_prefix", "/px4_bridge");

    vehicle_status_topic_ = this->declare_parameter<std::string>(
      "vehicle_status_topic", join_topic(fmu_prefix, "/out/vehicle_status"));
    vehicle_odometry_topic_ = this->declare_parameter<std::string>(
      "vehicle_odometry_topic", join_topic(fmu_prefix, "/out/vehicle_odometry"));
    battery_status_topic_ = this->declare_parameter<std::string>(
      "battery_status_topic", join_topic(fmu_prefix, "/out/battery_status"));
    vehicle_control_mode_topic_ = this->declare_parameter<std::string>(
      "vehicle_control_mode_topic", join_topic(fmu_prefix, "/out/vehicle_control_mode"));
    failsafe_flags_topic_ = this->declare_parameter<std::string>(
      "failsafe_flags_topic", join_topic(fmu_prefix, "/out/failsafe_flags"));
    timesync_status_topic_ = this->declare_parameter<std::string>(
      "timesync_status_topic", join_topic(fmu_prefix, "/out/timesync_status"));

    const auto state_topic = this->declare_parameter<std::string>(
      "state_topic", join_topic(bridge_prefix, "/state"));
    const auto odom_topic = this->declare_parameter<std::string>(
      "odom_topic", join_topic(bridge_prefix, "/odom"));
    const auto health_topic = this->declare_parameter<std::string>(
      "health_topic", join_topic(bridge_prefix, "/health"));

    odom_frame_id_ = this->declare_parameter<std::string>("odom_frame_id", "map");
    base_frame_id_ = this->declare_parameter<std::string>("base_frame_id", "base_link");
    publish_period_ms_ = this->declare_parameter<int>("publish_period_ms", 100);
    stale_timeout_ms_ = this->declare_parameter<int>("stale_timeout_ms", 1000);
    low_battery_threshold_ = this->declare_parameter<double>("low_battery_threshold", 0.20);

    state_pub_ = this->create_publisher<std_msgs::msg::String>(state_topic, 10);
    odom_pub_ = this->create_publisher<nav_msgs::msg::Odometry>(odom_topic, 10);
    health_pub_ = this->create_publisher<diagnostic_msgs::msg::DiagnosticArray>(health_topic, 10);

    vehicle_status_sub_ = this->create_subscription<px4_msgs::msg::VehicleStatus>(
      vehicle_status_topic_, px4_qos(),
      [this](const px4_msgs::msg::VehicleStatus::SharedPtr msg) {
        vehicle_status_ = *msg;
        status_received_at_ = std::chrono::steady_clock::now();
      });

    vehicle_odometry_sub_ = this->create_subscription<px4_msgs::msg::VehicleOdometry>(
      vehicle_odometry_topic_, px4_qos(),
      [this](const px4_msgs::msg::VehicleOdometry::SharedPtr msg) {
        vehicle_odometry_ = *msg;
        odometry_received_at_ = std::chrono::steady_clock::now();
      });

    battery_status_sub_ = this->create_subscription<px4_msgs::msg::BatteryStatus>(
      battery_status_topic_, px4_qos(),
      [this](const px4_msgs::msg::BatteryStatus::SharedPtr msg) {
        battery_status_ = *msg;
        battery_received_at_ = std::chrono::steady_clock::now();
      });

    vehicle_control_mode_sub_ = this->create_subscription<px4_msgs::msg::VehicleControlMode>(
      vehicle_control_mode_topic_, px4_qos(),
      [this](const px4_msgs::msg::VehicleControlMode::SharedPtr msg) {
        vehicle_control_mode_ = *msg;
        control_mode_received_at_ = std::chrono::steady_clock::now();
      });

    failsafe_flags_sub_ = this->create_subscription<px4_msgs::msg::FailsafeFlags>(
      failsafe_flags_topic_, px4_qos(),
      [this](const px4_msgs::msg::FailsafeFlags::SharedPtr msg) {
        failsafe_flags_ = *msg;
        failsafe_received_at_ = std::chrono::steady_clock::now();
      });

    timesync_status_sub_ = this->create_subscription<px4_msgs::msg::TimesyncStatus>(
      timesync_status_topic_, px4_qos(),
      [this](const px4_msgs::msg::TimesyncStatus::SharedPtr msg) {
        timesync_status_ = *msg;
        timesync_received_at_ = std::chrono::steady_clock::now();
      });

    timer_ = this->create_wall_timer(
      std::chrono::milliseconds(publish_period_ms_),
      std::bind(&Px4StatusAdapter::publish_outputs, this));
  }

private:
  using SteadyTimePoint = std::chrono::steady_clock::time_point;

  bool is_fresh(const SteadyTimePoint & received_at) const
  {
    if (received_at == SteadyTimePoint{}) {
      return false;
    }

    const auto age = std::chrono::steady_clock::now() - received_at;
    return age <= std::chrono::milliseconds(stale_timeout_ms_);
  }

  Px4VehicleState snapshot() const
  {
    Px4VehicleState state;
    state.has_status = vehicle_status_.has_value();
    state.has_odometry = vehicle_odometry_.has_value();
    state.has_battery = battery_status_.has_value();
    state.has_control_mode = vehicle_control_mode_.has_value();
    state.has_failsafe_flags = failsafe_flags_.has_value();
    state.has_timesync = timesync_status_.has_value();

    if (vehicle_status_) {
      state.armed =
        vehicle_status_->arming_state == px4_msgs::msg::VehicleStatus::ARMING_STATE_ARMED;
      state.failsafe = vehicle_status_->failsafe;
      state.preflight_checks_pass = vehicle_status_->pre_flight_checks_pass;
      state.nav_state = vehicle_status_->nav_state;
    }

    if (battery_status_) {
      state.battery_remaining = battery_status_->remaining;
    }

    if (vehicle_control_mode_) {
      state.offboard_enabled = vehicle_control_mode_->flag_control_offboard_enabled;
    }

    if (timesync_status_) {
      state.estimated_time_offset_us = timesync_status_->estimated_offset;
    }

    return state;
  }

  void publish_outputs()
  {
    publish_state();
    publish_health();
    publish_odometry();
  }

  void publish_state()
  {
    const auto state = snapshot();

    std_msgs::msg::String msg;
    std::ostringstream stream;
    stream << "{"
           << "\"status_fresh\":" << (is_fresh(status_received_at_) ? "true" : "false") << ","
           << "\"odometry_fresh\":" << (is_fresh(odometry_received_at_) ? "true" : "false") << ","
           << "\"armed\":" << (state.armed ? "true" : "false") << ","
           << "\"nav_state\":\"" << nav_state_to_string(state.nav_state) << "\","
           << "\"nav_state_id\":" << static_cast<int>(state.nav_state) << ","
           << "\"failsafe\":" << (state.failsafe ? "true" : "false") << ","
           << "\"offboard_enabled\":" << (state.offboard_enabled ? "true" : "false") << ","
           << "\"preflight_checks_pass\":" << (state.preflight_checks_pass ? "true" : "false")
           << ","
           << "\"battery_remaining\":" << state.battery_remaining << ","
           << "\"timesync_offset_us\":" << state.estimated_time_offset_us
           << "}";
    msg.data = stream.str();
    state_pub_->publish(msg);
  }

  void publish_health()
  {
    const auto state = snapshot();

    diagnostic_msgs::msg::DiagnosticStatus status;
    status.name = "px4_bridge/status";
    status.hardware_id = vehicle_status_ ?
      (std::to_string(vehicle_status_->system_id) + ":" +
      std::to_string(vehicle_status_->component_id)) :
      "px4:unknown";
    status.level = diagnostic_msgs::msg::DiagnosticStatus::OK;
    status.message = "PX4 bridge healthy";

    if (!is_fresh(status_received_at_)) {
      status.level = diagnostic_msgs::msg::DiagnosticStatus::ERROR;
      status.message = "vehicle_status stream missing or stale";
    } else if (!is_fresh(odometry_received_at_)) {
      status.level = diagnostic_msgs::msg::DiagnosticStatus::ERROR;
      status.message = "vehicle_odometry stream missing or stale";
    } else if (state.failsafe) {
      status.level = diagnostic_msgs::msg::DiagnosticStatus::ERROR;
      status.message = "PX4 reported failsafe";
    } else if (state.has_failsafe_flags && failsafe_flags_->offboard_control_signal_lost) {
      status.level = diagnostic_msgs::msg::DiagnosticStatus::WARN;
      status.message = "Offboard signal lost";
    } else if (
      state.has_battery && std::isfinite(state.battery_remaining) &&
      state.battery_remaining >= 0.0F &&
      state.battery_remaining < static_cast<float>(low_battery_threshold_))
    {
      status.level = diagnostic_msgs::msg::DiagnosticStatus::WARN;
      status.message = "Battery below configured threshold";
    } else if (state.has_status && !state.preflight_checks_pass) {
      status.level = diagnostic_msgs::msg::DiagnosticStatus::WARN;
      status.message = "Preflight checks not passing";
    }

    status.values.push_back(
      key_value("vehicle_status_topic", vehicle_status_topic_));
    status.values.push_back(
      key_value("vehicle_odometry_topic", vehicle_odometry_topic_));
    status.values.push_back(
      key_value("status_fresh", is_fresh(status_received_at_) ? "true" : "false"));
    status.values.push_back(
      key_value("odometry_fresh", is_fresh(odometry_received_at_) ? "true" : "false"));
    status.values.push_back(
      key_value("armed", state.armed ? "true" : "false"));
    status.values.push_back(
      key_value("nav_state", nav_state_to_string(state.nav_state)));
    status.values.push_back(
      key_value("offboard_enabled", state.offboard_enabled ? "true" : "false"));
    status.values.push_back(
      key_value("failsafe", state.failsafe ? "true" : "false"));
    status.values.push_back(
      key_value("battery_remaining", std::to_string(state.battery_remaining)));
    status.values.push_back(
      key_value("timesync_offset_us", std::to_string(state.estimated_time_offset_us)));

    if (state.has_failsafe_flags) {
      status.values.push_back(
        key_value(
          "offboard_signal_lost",
          failsafe_flags_->offboard_control_signal_lost ? "true" : "false"));
      status.values.push_back(
        key_value(
          "local_position_invalid",
          failsafe_flags_->local_position_invalid ? "true" : "false"));
      status.values.push_back(
        key_value(
          "manual_control_signal_lost",
          failsafe_flags_->manual_control_signal_lost ? "true" : "false"));
    }

    diagnostic_msgs::msg::DiagnosticArray msg;
    msg.header.stamp = this->now();
    msg.status.push_back(status);
    health_pub_->publish(msg);
  }

  void publish_odometry()
  {
    if (!vehicle_odometry_ || !is_fresh(odometry_received_at_)) {
      return;
    }

    nav_msgs::msg::Odometry msg;
    msg.header.stamp = this->now();
    msg.header.frame_id = odom_frame_id_;
    msg.child_frame_id = base_frame_id_;
    msg.pose.pose.position = ned_to_enu_position(vehicle_odometry_->position);
    msg.pose.pose.orientation = px4_to_ros_orientation(vehicle_odometry_->q);

    if (
      vehicle_odometry_->velocity_frame ==
      px4_msgs::msg::VehicleOdometry::VELOCITY_FRAME_BODY_FRD)
    {
      msg.twist.twist.linear = frd_to_flu_vector(vehicle_odometry_->velocity);
    } else {
      msg.twist.twist.linear = ned_to_enu_vector(vehicle_odometry_->velocity);
    }

    msg.twist.twist.angular = frd_to_flu_vector(vehicle_odometry_->angular_velocity);

    set_pose_covariance(
      msg.pose.covariance.data(),
      vehicle_odometry_->position_variance,
      vehicle_odometry_->orientation_variance);
    set_twist_covariance(
      msg.twist.covariance.data(),
      vehicle_odometry_->velocity_variance);

    odom_pub_->publish(msg);
  }

  std::string vehicle_status_topic_;
  std::string vehicle_odometry_topic_;
  std::string battery_status_topic_;
  std::string vehicle_control_mode_topic_;
  std::string failsafe_flags_topic_;
  std::string timesync_status_topic_;
  std::string odom_frame_id_;
  std::string base_frame_id_;
  int publish_period_ms_{100};
  int stale_timeout_ms_{1000};
  double low_battery_threshold_{0.20};

  std::optional<px4_msgs::msg::VehicleStatus> vehicle_status_;
  std::optional<px4_msgs::msg::VehicleOdometry> vehicle_odometry_;
  std::optional<px4_msgs::msg::BatteryStatus> battery_status_;
  std::optional<px4_msgs::msg::VehicleControlMode> vehicle_control_mode_;
  std::optional<px4_msgs::msg::FailsafeFlags> failsafe_flags_;
  std::optional<px4_msgs::msg::TimesyncStatus> timesync_status_;

  SteadyTimePoint status_received_at_;
  SteadyTimePoint odometry_received_at_;
  SteadyTimePoint battery_received_at_;
  SteadyTimePoint control_mode_received_at_;
  SteadyTimePoint failsafe_received_at_;
  SteadyTimePoint timesync_received_at_;

  rclcpp::Publisher<std_msgs::msg::String>::SharedPtr state_pub_;
  rclcpp::Publisher<nav_msgs::msg::Odometry>::SharedPtr odom_pub_;
  rclcpp::Publisher<diagnostic_msgs::msg::DiagnosticArray>::SharedPtr health_pub_;

  rclcpp::Subscription<px4_msgs::msg::VehicleStatus>::SharedPtr vehicle_status_sub_;
  rclcpp::Subscription<px4_msgs::msg::VehicleOdometry>::SharedPtr vehicle_odometry_sub_;
  rclcpp::Subscription<px4_msgs::msg::BatteryStatus>::SharedPtr battery_status_sub_;
  rclcpp::Subscription<px4_msgs::msg::VehicleControlMode>::SharedPtr vehicle_control_mode_sub_;
  rclcpp::Subscription<px4_msgs::msg::FailsafeFlags>::SharedPtr failsafe_flags_sub_;
  rclcpp::Subscription<px4_msgs::msg::TimesyncStatus>::SharedPtr timesync_status_sub_;
  rclcpp::TimerBase::SharedPtr timer_;
};

}  // namespace venom_px4_bridge

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<venom_px4_bridge::Px4StatusAdapter>());
  rclcpp::shutdown();
  return 0;
}
