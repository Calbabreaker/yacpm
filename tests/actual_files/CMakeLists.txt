cmake_minimum_required(VERSION 3.12 FATAL_ERROR)
project(use_actual_files)

# force get files from remote
file(REMOVE ${CMAKE_BINARY_DIR}/yacpm.cmake)
file(REMOVE ${CMAKE_BINARY_DIR}/yacpm_extended.cmake)
file(REMOVE ${CMAKE_BINARY_DIR}/yacpm.py)

include(../test_project.cmake)
