cmake_minimum_required(VERSION 3.12 FATAL_ERROR)
project(UseActualRemote)

# force get files from remote
file(REMOVE ${CMAKE_BINARY_DIR}/yacpm.cmake)

include(../test_project.cmake)
