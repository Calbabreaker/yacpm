cmake_minimum_required(VERSION 3.12 FATAL_ERROR)
project(Window)

include(${CMAKE_BINARY_DIR}/yacpm.cmake)

add_executable(${PROJECT_NAME} main.cpp)

target_link_libraries(${PROJECT_NAME} ${YACPM_LIBS} GL)
