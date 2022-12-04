cmake_minimum_required(VERSION 3.12 FATAL_ERROR)
project(library_using_yacpm)

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
set(YACPM_LIBRARY_TEST "lets go" CACHE STRING "" FORCE)

add_subdirectory(test_library)

add_executable(${PROJECT_NAME} main.cpp)
target_link_libraries(${PROJECT_NAME} yacpm_library_test)
