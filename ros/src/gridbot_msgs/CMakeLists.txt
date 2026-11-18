cmake_minimum_required(VERSION 3.8)
project(gridbot_msgs)

find_package(ament_cmake REQUIRED)
find_package(builtin_interfaces REQUIRED)
find_package(rosidl_default_generators REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/Telemetry.msg"
  DEPENDENCIES builtin_interfaces
)
ament_export_dependencies(rosidl_default_runtime)

if(BUILD_TESTING)
  find_package(ament_cmake_pytest REQUIRED)
  ament_add_pytest_test(telemetry test/test_telemetry.py
    APPEND_ENV PYTHONPATH=${CMAKE_CURRENT_BINARY_DIR}/rosidl_generator_py
    APPEND_LIBRARY_DIRS ${CMAKE_CURRENT_BINARY_DIR}
  )
endif()

ament_package()
