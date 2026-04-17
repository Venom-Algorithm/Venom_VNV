cmake_minimum_required(VERSION 3.8)
project(venom_px4_bridge)

if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(diagnostic_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(px4_msgs REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(tf2 REQUIRED)
find_package(tf2_geometry_msgs REQUIRED)

add_library(${PROJECT_NAME}_core
  src/frame_conversions.cpp
)
target_include_directories(${PROJECT_NAME}_core PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)
ament_target_dependencies(${PROJECT_NAME}_core
  geometry_msgs
  tf2
  tf2_geometry_msgs
)

add_executable(px4_status_adapter
  src/px4_status_adapter.cpp
)
target_link_libraries(px4_status_adapter ${PROJECT_NAME}_core)
target_include_directories(px4_status_adapter PRIVATE include)
ament_target_dependencies(px4_status_adapter
  diagnostic_msgs
  geometry_msgs
  nav_msgs
  px4_msgs
  rclcpp
  std_msgs
  tf2
  tf2_geometry_msgs
)

add_executable(px4_agent_monitor
  src/px4_agent_monitor.cpp
)
target_include_directories(px4_agent_monitor PRIVATE include)
ament_target_dependencies(px4_agent_monitor
  diagnostic_msgs
  px4_msgs
  rclcpp
)

install(
  TARGETS
    ${PROJECT_NAME}_core
    px4_status_adapter
    px4_agent_monitor
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION lib/${PROJECT_NAME}
)

install(
  DIRECTORY include/
  DESTINATION include
)

install(
  DIRECTORY launch config
  DESTINATION share/${PROJECT_NAME}
)

ament_export_include_directories(include)
ament_export_dependencies(
  diagnostic_msgs
  geometry_msgs
  nav_msgs
  px4_msgs
  rclcpp
  std_msgs
  tf2
  tf2_geometry_msgs
)

ament_package()
