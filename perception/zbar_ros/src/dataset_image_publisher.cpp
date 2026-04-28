#include <algorithm>
#include <chrono>
#include <cctype>
#include <filesystem>
#include <functional>
#include <string>
#include <vector>

#include "cv_bridge/cv_bridge.h"
#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/image.hpp"
#include "std_msgs/msg/header.hpp"
#include <opencv2/imgcodecs.hpp>

namespace zbar_ros
{
namespace fs = std::filesystem;
using namespace std::chrono_literals;

class DatasetImagePublisher : public rclcpp::Node
{
public:
  DatasetImagePublisher()
  : Node("dataset_image_publisher")
  {
    dataset_path_ = this->declare_parameter<std::string>("dataset_path", "");
    frame_id_ = this->declare_parameter<std::string>("frame_id", "dataset_camera_optical_frame");
    publish_interval_seconds_ = this->declare_parameter<double>("publish_interval_seconds", 1.0);
    if (publish_interval_seconds_ <= 0.0) {
      RCLCPP_WARN(
        get_logger(),
        "Parameter 'publish_interval_seconds' must be positive, using 1.0 instead");
      publish_interval_seconds_ = 1.0;
    }

    image_pub_ = this->create_publisher<sensor_msgs::msg::Image>("image", 10);

    loadImageFiles();

    if (image_files_.empty()) {
      RCLCPP_WARN(get_logger(), "No dataset images available in '%s'", dataset_path_.c_str());
      return;
    }

    const auto publish_period = std::chrono::duration_cast<std::chrono::nanoseconds>(
      std::chrono::duration<double>(publish_interval_seconds_));
    timer_ = this->create_wall_timer(
      publish_period, std::bind(&DatasetImagePublisher::publishImage, this));
  }

private:
  static bool hasSupportedExtension(const fs::path & path)
  {
    std::string extension = path.extension().string();
    std::transform(
      extension.begin(), extension.end(), extension.begin(),
      [](unsigned char c) {return static_cast<char>(std::tolower(c));});
    return extension == ".png" || extension == ".jpg" || extension == ".jpeg";
  }

  void loadImageFiles()
  {
    if (dataset_path_.empty()) {
      RCLCPP_WARN(get_logger(), "Parameter 'dataset_path' is empty");
      return;
    }

    if (!fs::exists(dataset_path_)) {
      RCLCPP_WARN(get_logger(), "Dataset path does not exist: %s", dataset_path_.c_str());
      return;
    }

    if (!fs::is_directory(dataset_path_)) {
      RCLCPP_WARN(get_logger(), "Dataset path is not a directory: %s", dataset_path_.c_str());
      return;
    }

    for (const auto & entry : fs::directory_iterator(dataset_path_)) {
      if (entry.is_regular_file() && hasSupportedExtension(entry.path())) {
        image_files_.push_back(entry.path());
      }
    }

    std::sort(image_files_.begin(), image_files_.end());
    RCLCPP_INFO(
      get_logger(), "Loaded %zu dataset images from '%s'",
      image_files_.size(), dataset_path_.c_str());
  }

  void publishImage()
  {
    if (image_files_.empty()) {
      return;
    }

    const fs::path & image_path = image_files_.at(current_image_index_);
    current_image_index_ = (current_image_index_ + 1) % image_files_.size();

    const auto image = cv::imread(image_path.string(), cv::IMREAD_COLOR);
    if (image.empty()) {
      RCLCPP_WARN(get_logger(), "Failed to load image: %s", image_path.c_str());
      return;
    }

    std_msgs::msg::Header header;
    header.stamp = now();
    header.frame_id = frame_id_;

    auto message = cv_bridge::CvImage(header, "bgr8", image).toImageMsg();
    image_pub_->publish(*message);
    RCLCPP_DEBUG(get_logger(), "Published dataset image: %s", image_path.c_str());
  }

  rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr image_pub_;
  rclcpp::TimerBase::SharedPtr timer_;
  std::vector<fs::path> image_files_;
  std::string dataset_path_;
  std::string frame_id_;
  double publish_interval_seconds_{1.0};
  size_t current_image_index_{0};
};

}  // namespace zbar_ros

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<zbar_ros::DatasetImagePublisher>());
  rclcpp::shutdown();
  return 0;
}
