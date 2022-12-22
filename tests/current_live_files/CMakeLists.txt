cmake_minimum_required(VERSION 3.12 FATAL_ERROR)
project(current_lives_files)

# Force get files from live remote
file(REMOVE ${CMAKE_BINARY_DIR}/yacpm.cmake)
file(REMOVE ${CMAKE_BINARY_DIR}/yacpm_extended.cmake)
file(REMOVE ${CMAKE_BINARY_DIR}/yacpm.py)

include(../test_project.cmake)
