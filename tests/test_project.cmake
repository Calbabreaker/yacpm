if(NOT EXISTS "${CMAKE_CURRENT_BINARY_DIR}/yacpm.cmake")
    file(DOWNLOAD "https://github.com/Calbabreaker/yacpm/raw/v1/yacpm.cmake" "${CMAKE_CURRENT_BINARY_DIR}/yacpm.cmake")
endif()

include(${CMAKE_CURRENT_BINARY_DIR}/yacpm.cmake)
yacpm_use_extended()

add_executable(${PROJECT_NAME} main.cpp)
yacpm_target_warnings(${PROJECT_NAME} PRIVATE)

target_link_libraries(${PROJECT_NAME} ${YACPM_PKGS})
