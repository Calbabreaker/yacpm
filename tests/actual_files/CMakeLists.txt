cmake_minimum_required(VERSION 3.12 FATAL_ERROR)
project(UseActualRemote)

# force get files from remote
file(GLOB YACPM_FILES ${CMAKE_BINARY_DIR}/*.py ${CMAKE_BINARY_DIR}/*.cmake)
file(REMOVE ${YACPM_FILES})

include(../test_project.cmake)
