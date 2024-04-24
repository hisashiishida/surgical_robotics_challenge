cmake_minimum_required (VERSION 3.1)
project (surgical_robotics_challenge)

set(CMAKE_CXX_STANDARD 11)

find_package(AMBF)
find_package(Boost COMPONENTS program_options filesystem)


include_directories(${AMBF_INCLUDE_DIRS})
include_directories(${Boost_INCLUDE_DIRS})
include_directories(${catkin_INCLUDE_DIRS})

link_directories(${AMBF_LIBRARY_DIRS})

add_definitions(${AMBF_DEFINITIONS})


message("---> LIBS " ${catkin_INCLUDE_DIRS})
message("---> FOUND ? " ${catkin_vdrilling_msgs_FOUND})

add_library(camera_projection_override SHARED 
    plugins/camera_projection_override/projection_override.cpp
    plugins/camera_projection_override/projection_override.h)

target_link_libraries(camera_projection_override ${AMBF_LIBRARIES})
set_property(TARGET camera_projection_override PROPERTY POSITION_INDEPENDENT_CODE TRUE)