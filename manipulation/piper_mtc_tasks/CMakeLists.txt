cmake_minimum_required(VERSION 3.8)
project(piper_mtc_tasks)

if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(gazebo_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(linkattacher_msgs REQUIRED)
find_package(moveit_ros_planning REQUIRED)
find_package(moveit_ros_planning_interface REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclcpp_action REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(tf2 REQUIRED)
find_package(tf2_geometry_msgs REQUIRED)
find_package(trajectory_msgs REQUIRED)
find_package(venom_manipulation_interfaces REQUIRED)

find_package(moveit_task_constructor_core QUIET)
find_package(moveit_task_constructor_msgs QUIET)

set(common_dependencies
  gazebo_msgs
  geometry_msgs
  linkattacher_msgs
  moveit_ros_planning
  moveit_ros_planning_interface
  rclcpp
  rclcpp_action
  sensor_msgs
  tf2
  tf2_geometry_msgs
  trajectory_msgs
  venom_manipulation_interfaces
)

if(moveit_task_constructor_core_FOUND AND moveit_task_constructor_msgs_FOUND)
  set(runtime_targets pick_place_server ik_frame_sweep)

  add_library(${PROJECT_NAME}_core
    src/gripper_stage_builder.cpp
    src/scene_manager.cpp
    src/stage_builders.cpp
    src/task_factory.cpp
    src/pick_task.cpp
    src/place_task.cpp
  )
  target_include_directories(${PROJECT_NAME}_core PUBLIC
    include
  )
  ament_target_dependencies(${PROJECT_NAME}_core
    ${common_dependencies}
    moveit_task_constructor_core
    moveit_task_constructor_msgs
  )

  add_executable(pick_place_server
    src/pick_place_server.cpp
  )
  target_include_directories(pick_place_server PUBLIC
    include
  )
  target_link_libraries(pick_place_server
    ${PROJECT_NAME}_core
  )
  ament_target_dependencies(pick_place_server
    ${common_dependencies}
    moveit_task_constructor_core
    moveit_task_constructor_msgs
  )

  add_executable(ik_frame_sweep
    src/ik_frame_sweep.cpp
  )
  target_include_directories(ik_frame_sweep PUBLIC
    include
  )
  ament_target_dependencies(ik_frame_sweep
    geometry_msgs
    moveit_ros_planning
    rclcpp
  )

else()
  set(runtime_targets pick_place_server)

  message(WARNING
    "MoveIt Task Constructor dependencies were not found. "
    "Building a stub piper_mtc_tasks server instead. Install "
    "moveit_task_constructor_core and moveit_task_constructor_msgs "
    "to enable the real implementation.")

  add_executable(pick_place_server
    src/pick_place_server_stub.cpp
  )
  target_include_directories(pick_place_server PUBLIC
    include
  )
  ament_target_dependencies(pick_place_server
    rclcpp
    venom_manipulation_interfaces
  )
endif()

install(
  TARGETS ${runtime_targets}
  RUNTIME DESTINATION lib/${PROJECT_NAME}
)

install(
  PROGRAMS scripts/pivot_tcp_calibration.py
  DESTINATION lib/${PROJECT_NAME}
)

install(
  DIRECTORY include/
  DESTINATION include
)

install(
  DIRECTORY config launch
  DESTINATION share/${PROJECT_NAME}
)

ament_export_include_directories(include)
ament_package()
