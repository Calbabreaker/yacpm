file(GLOB_RECURSE ENTT_SOURCES repository/src/*.hpp)
add_library(entt ${ENTT_SOURCES})

set_target_properties(entt PROPERTIES LINKER_LANGUAGE CXX)
target_include_directories(entt SYSTEM PUBLIC repository/src)
