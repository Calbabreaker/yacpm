include(repository/CMake/utility.cmake)
include(repository/CMake/config.cmake)

set(BUILD_STATIC ON)
add_subdirectory(repository/src/rttr)

add_library(rttr ALIAS rttr_core_lib)
