cmake_minimum_required(VERSION 3.8)
project(zbar_ros)

if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Find dependencies
find_package(ament_cmake REQUIRED)
find_package(cv_bridge REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(OpenCV REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(zbar_interfaces REQUIRED)

add_library(barcode_reader_node src/barcode_reader_node.cpp)
target_include_directories(barcode_reader_node PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>)
ament_target_dependencies(barcode_reader_node
  cv_bridge
  geometry_msgs
  rclcpp
  sensor_msgs
  zbar_interfaces)
target_link_libraries(barcode_reader_node
  ${OpenCV_LIBRARIES}
  zbar)

add_executable(qr_code_detector src/barcode_reader_main.cpp)
ament_target_dependencies(qr_code_detector rclcpp)
target_link_libraries(qr_code_detector barcode_reader_node)

add_executable(dataset_image_publisher src/dataset_image_publisher.cpp)
target_include_directories(dataset_image_publisher PRIVATE ${OpenCV_INCLUDE_DIRS})
ament_target_dependencies(dataset_image_publisher
  cv_bridge
  rclcpp
  sensor_msgs
)
target_link_libraries(dataset_image_publisher ${OpenCV_LIBRARIES})

install(TARGETS
  qr_code_detector
  dataset_image_publisher
  barcode_reader_node
  EXPORT export_${PROJECT_NAME}
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION lib/${PROJECT_NAME})
install(DIRECTORY launch/
  DESTINATION share/${PROJECT_NAME}/launch
  FILES_MATCHING PATTERN "*.launch.py")
install(DIRECTORY data/
  DESTINATION share/${PROJECT_NAME}/data)
install(DIRECTORY include/
  DESTINATION include/)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)

  # Skip copyright check, because the copyright used is not recognised by ament_copyright
  set(ament_cmake_copyright_FOUND TRUE)

  ament_lint_auto_find_test_dependencies()
endif()

ament_export_dependencies(
  cv_bridge
  geometry_msgs
  OpenCV
  rclcpp
  sensor_msgs
  zbar_interfaces)
ament_export_include_directories(include)
ament_export_targets(export_${PROJECT_NAME} HAS_LIBRARY_TARGET)
ament_package()
