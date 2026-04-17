#include <chrono>
#include <optional>
#include <set>
#include <string>
#include <unordered_set>
#include <utility>
#include <vector>

#include "diagnostic_msgs/msg/diagnostic_array.hpp"
#include "diagnostic_msgs/msg/diagnostic_status.hpp"
#include "diagnostic_msgs/msg/key_value.hpp"
#include "px4_msgs/msg/timesync_status.hpp"
#include "rclcpp/rclcpp.hpp"

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

}  // namespace

class Px4AgentMonitor : public rclcpp::Node
{
public:
  Px4AgentMonitor()
  : Node("px4_agent_monitor")
  {
    const auto fmu_prefix = this->declare_parameter<std::string>("fmu_prefix", "/fmu");
    const auto bridge_prefix = this->declare_parameter<std::string>("bridge_prefix", "/px4_bridge");

    timesync_topic_ = this->declare_parameter<std::string>(
      "timesync_topic", join_topic(fmu_prefix, "/out/timesync_status"));
    agent_status_topic_ = this->declare_parameter<std::string>(
      "agent_status_topic", join_topic(bridge_prefix, "/agent_status"));
    publish_period_ms_ = this->declare_parameter<int>("publish_period_ms", 1000);
    timesync_timeout_ms_ = this->declare_parameter<int>("timesync_timeout_ms", 1500);
    required_topics_ = this->declare_parameter<std::vector<std::string>>(
      "required_topics",
      std::vector<std::string>{
        join_topic(fmu_prefix, "/out/vehicle_status"),
        join_topic(fmu_prefix, "/out/vehicle_odometry"),
        join_topic(fmu_prefix, "/out/timesync_status"),
      });

    agent_status_pub_ = this->create_publisher<diagnostic_msgs::msg::DiagnosticArray>(
      agent_status_topic_, 10);

    timesync_sub_ = this->create_subscription<px4_msgs::msg::TimesyncStatus>(
      timesync_topic_, px4_qos(),
      [this](const px4_msgs::msg::TimesyncStatus::SharedPtr msg) {
        last_timesync_ = *msg;
        last_timesync_received_at_ = std::chrono::steady_clock::now();
      });

    timer_ = this->create_wall_timer(
      std::chrono::milliseconds(publish_period_ms_),
      std::bind(&Px4AgentMonitor::publish_status, this));
  }

private:
  using SteadyTimePoint = std::chrono::steady_clock::time_point;

  bool timesync_fresh() const
  {
    if (last_timesync_received_at_ == SteadyTimePoint{}) {
      return false;
    }

    const auto age = std::chrono::steady_clock::now() - last_timesync_received_at_;
    return age <= std::chrono::milliseconds(timesync_timeout_ms_);
  }

  void publish_status()
  {
    std::unordered_set<std::string> topics_present;
    for (const auto & item : this->get_topic_names_and_types()) {
      topics_present.insert(item.first);
    }

    std::set<std::string> missing_topics;
    for (const auto & topic : required_topics_) {
      if (topics_present.find(topic) == topics_present.end()) {
        missing_topics.insert(topic);
      }
    }

    diagnostic_msgs::msg::DiagnosticStatus status;
    status.name = "px4_bridge/agent_monitor";
    status.hardware_id = "uxrce_dds_agent";
    status.level = diagnostic_msgs::msg::DiagnosticStatus::OK;
    status.message = "PX4 DDS topics visible and timesync healthy";

    if (!missing_topics.empty()) {
      status.level = diagnostic_msgs::msg::DiagnosticStatus::WARN;
      status.message = "Required PX4 DDS topics are missing";
    } else if (!timesync_fresh()) {
      status.level = diagnostic_msgs::msg::DiagnosticStatus::WARN;
      status.message = "DDS topics visible but timesync is stale";
    }

    status.values.push_back(
      key_value("agent_status_topic", agent_status_topic_));
    status.values.push_back(
      key_value("timesync_topic", timesync_topic_));
    status.values.push_back(
      key_value("timesync_fresh", timesync_fresh() ? "true" : "false"));
    status.values.push_back(
      key_value("required_topic_count", std::to_string(required_topics_.size())));
    status.values.push_back(
      key_value("missing_topic_count", std::to_string(missing_topics.size())));

    for (const auto & topic : required_topics_) {
      const auto present = missing_topics.find(topic) == missing_topics.end();
      status.values.push_back(
        key_value(topic, present ? "present" : "missing"));
    }

    if (last_timesync_) {
      status.values.push_back(
        key_value("estimated_offset_us", std::to_string(last_timesync_->estimated_offset)));
      status.values.push_back(
        key_value("round_trip_time_us", std::to_string(last_timesync_->round_trip_time)));
    }

    const auto summary = status.message + ":" + std::to_string(status.level) + ":" +
      std::to_string(missing_topics.size());
    if (summary != last_summary_) {
      last_summary_ = summary;
      if (status.level == diagnostic_msgs::msg::DiagnosticStatus::OK) {
        RCLCPP_INFO(this->get_logger(), "%s", status.message.c_str());
      } else {
        RCLCPP_WARN(this->get_logger(), "%s", status.message.c_str());
      }
    }

    diagnostic_msgs::msg::DiagnosticArray msg;
    msg.header.stamp = this->now();
    msg.status.push_back(status);
    agent_status_pub_->publish(msg);
  }

  std::string timesync_topic_;
  std::string agent_status_topic_;
  int publish_period_ms_{1000};
  int timesync_timeout_ms_{1500};
  std::vector<std::string> required_topics_;
  std::string last_summary_;

  std::optional<px4_msgs::msg::TimesyncStatus> last_timesync_;
  SteadyTimePoint last_timesync_received_at_;

  rclcpp::Publisher<diagnostic_msgs::msg::DiagnosticArray>::SharedPtr agent_status_pub_;
  rclcpp::Subscription<px4_msgs::msg::TimesyncStatus>::SharedPtr timesync_sub_;
  rclcpp::TimerBase::SharedPtr timer_;
};

}  // namespace venom_px4_bridge

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<venom_px4_bridge::Px4AgentMonitor>());
  rclcpp::shutdown();
  return 0;
}
