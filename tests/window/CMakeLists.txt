cmake_minimum_required(VERSION 3.12 FATAL_ERROR)
project(Window)

if(NOT EXISTS "${CMAKE_CURRENT_BINARY_DIR}/yacpm.cmake")
    file(DOWNLOAD "https://github.com/Calbabreaker/yacpm/raw/main/yacpm.cmake" "${CMAKE_CURRENT_BINARY_DIR}/yacpm.py")
endif()

include(${CMAKE_CURRENT_BINARY_DIR}/yacpm.cmake)

add_executable(${PROJECT_NAME} main.cpp)

target_link_libraries(${PROJECT_NAME} ${YACPM_LIBS} GL)
