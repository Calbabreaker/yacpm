cmake_minimum_required(VERSION 3.12 FATAL_ERROR)
project(ImGuiWindow)

if(NOT EXISTS "${CMAKE_BINARY_DIR}/yacpm.cmake")
    file(DOWNLOAD "https://github.com/Calbabreaker/yacpm/raw/v3/yacpm.cmake" "${CMAKE_BINARY_DIR}/yacpm.cmake")
endif()

include(${CMAKE_BINARY_DIR}/yacpm.cmake)
yacpm_use_extended()

add_executable(${PROJECT_NAME} main.cpp)
yacpm_target_warnings(${PROJECT_NAME} PRIVATE)

target_link_libraries(${PROJECT_NAME} ${YACPM_PACKAGES})
