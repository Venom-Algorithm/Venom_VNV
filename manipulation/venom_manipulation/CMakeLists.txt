cmake_minimum_required(VERSION 3.8)
project(venom_manipulation)

if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(builtin_interfaces REQUIRED)
find_package(controller_manager_msgs REQUIRED)
find_package(control_msgs REQUIRED)
find_package(gazebo_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(moveit_msgs REQUIRED)
find_package(moveit_ros_planning_interface REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclcpp_action REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(std_msgs REQUIRED)
find_package(tf2 REQUIRED)
find_package(tf2_geometry_msgs REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(venom_manipulation_interfaces REQUIRED)

add_executable(manipulation_commander
  src/manipulation_commander.cpp
)

ament_target_dependencies(manipulation_commander
  builtin_interfaces
  controller_manager_msgs
  control_msgs
  gazebo_msgs
  geometry_msgs
  moveit_msgs
  moveit_ros_planning_interface
  rclcpp
  rclcpp_action
  sensor_msgs
  std_msgs
  tf2
  tf2_geometry_msgs
  tf2_ros
  venom_manipulation_interfaces
)

install(
  TARGETS manipulation_commander
  RUNTIME DESTINATION lib/${PROJECT_NAME}
)

install(
  DIRECTORY launch config models
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
