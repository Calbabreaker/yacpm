include(repository/CMake/utility.cmake)
include(repository/CMake/config.cmake)

if (NOT BUILD_SHARED_LIBS)
    set(BUILD_STATIC ON CACHE BOOL "" FORCE)
else()
    set(BUILD_STATIC OFF CACHE BOOL "" FORCE)
endif()
set(BUILD_RTTR_DYNAMIC ${BUILD_SHARED_LIBS} CACHE BOOL "" FORCE)
set(BUILD_PACKAGE OFF CACHE BOOL "" FORCE)
add_subdirectory(repository/src/rttr)

if(TARGET rttr_core)
    # dynamic lib
    set(RTTR_TARGET_USED rttr_core)
elseif(TARGET rttr_core_lib)
    # static lib
    set(RTTR_TARGET_USED rttr_core_lib)
endif()

target_include_directories(${RTTR_TARGET_USED} SYSTEM PUBLIC repository/src)
add_library(rttr ALIAS ${RTTR_TARGET_USED})
