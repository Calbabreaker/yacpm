file(GLOB_RECURSE RAYLIB_CPP_SOURCES repository/include/*.hpp)
add_library(raylib_cpp ${RAYLIB_CPP_SOURCES})

set_target_properties(raylib_cpp PROPERTIES LINKER_LANGUAGE CXX)
target_include_directories(raylib_cpp SYSTEM PUBLIC repository/include/)