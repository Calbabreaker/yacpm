include(repository/CMake/utility.cmake)
include(repository/CMake/config.cmake)

set(BUILD_STATIC NOT BUILD_SHARED_LIBS CACHE BOOL "" FORCE)
set(BUILD_RTTR_DYNAMIC BUILD_SHARED_LIBS CACHE BOOL "" FORCE)
set(BUILD_PACKAGE OFF CACHE BOOL "" FORCE)
add_subdirectory(repository/src/rttr)

set(RTTR_LIB_USED 
    $<TARGET_NAME_IF_EXISTS:rttr_core>
    $<TARGET_NAME_IF_EXISTS:rttr_core_lib>)

target_include_directories(${RTTR_LIB_USED} SYSTEM PUBLIC repository/src)
add_library(rttr ALIAS ${RTTR_LIB_USED}
