add_subdirectory(repository)

file(GLOB_RECURSE SFML_SOURCES repository/include/SFML/*.hpp)

add_library(sfml ${SFML_SOURCES})
target_link_libraries(sfml sfml-graphics sfml-audio sfml-system sfml-graphics sfml-window sfml-network)
target_include_directories(sfml SYSTEM PUBLIC repository/include)
set_target_properties(sfml PROPERTIES LINKER_LANGUAGE CXX)
