cmake_minimum_required(VERSION 3.12 FATAL_ERROR)
project(yacpm_library_test)

# set YACPM_LIBRARY_TEST to "lets go" to sucessfully build
option(YACPM_LIBRARY_TEST "no set")

if(NOT YACPM_LIBRARY_TEST STREQUAL "lets go")
    message(FATAL_ERROR "YACPM_LIBRARY_TEST needs to be value 'lets go'")
endif()

if(NOT EXISTS "${CMAKE_BINARY_DIR}/yacpm.cmake")
    file(DOWNLOAD "https://github.com/Calbabreaker/yacpm/raw/v3/yacpm.cmake" "${CMAKE_BINARY_DIR}/yacpm.cmake")
endif()

include(${CMAKE_BINARY_DIR}/yacpm.cmake)

add_library(${PROJECT_NAME} yacpm_library_test.cpp yacpm_library_test.h)
target_include_directories(${PROJECT_NAME} PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
target_link_libraries(${PROJECT_NAME} glm)
