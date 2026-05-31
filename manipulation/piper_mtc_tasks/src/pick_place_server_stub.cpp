#include <memory>

#include <rclcpp/rclcpp.hpp>

class PickPlaceServerStub : public rclcpp::Node
{
public:
  PickPlaceServerStub()
  : Node("pick_place_server")
  {
    RCLCPP_ERROR(
      get_logger(),
      "MoveIt Task Constructor dependencies are not installed in this environment. "
      "Install moveit_task_constructor_core and moveit_task_constructor_msgs, "
      "then rebuild piper_mtc_tasks to enable the real server.");
  }
};

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<PickPlaceServerStub>());
  rclcpp::shutdown();
  return 0;
}
