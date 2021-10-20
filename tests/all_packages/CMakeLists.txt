cmake_minimum_required(VERSION 3.12 FATAL_ERROR)
project(CustomPackage)

execute_process(
    COMMAND python3 ${CMAKE_CURRENT_SOURCE_DIR}/get_all_packages.py
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
)

add_custom_command(
    OUTPUT conflicting/build/bin fake.file
    COMMAND python3 ${CMAKE_CURRENT_SOURCE_DIR}/../run_test.py all_packages/conflicting
    DEPENDS ${PROJECT_NAME}
)

add_custom_target(
    conflicting ALL
    DEPENDS fake.file
)

include(../test_project.cmake)
