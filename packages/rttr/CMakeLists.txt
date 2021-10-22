include(repository/CMake/utility.cmake)
include(repository/CMake/config.cmake)

set(BUILD_STATIC ON CACHE BOOL "" FORCE)
set(BUILD_RTTR_DYNAMIC OFF CACHE BOOL "" FORCE)
set(BUILD_PACKAGE OFF CACHE BOOL "" FORCE)
add_subdirectory(repository/src/rttr)

target_include_directories(rttr_core_lib SYSTEM PUBLIC repository/src)
add_library(rttr ALIAS rttr_core_lib)
