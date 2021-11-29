file(GLOB_RECURSE NLOHMANN_JSON_SOURCES repository/include/nlohmann/*.hpp)
add_library(nlohmann_json ${NLOHMANN_JSON_SOURCES})

set_target_properties(nlohmann_json PROPERTIES LINKER_LANGUAGE CXX)
target_include_directories(nlohmann_json SYSTEM PUBLIC repository/include)