add_subdirectory(repository)

file(GLOB SFML_SOURCES repository/include/SFML/*.hpp)

add_library(sfml ${SFML_SOURCES})
target_link_libraries(sfml sfml-graphics sfml-audio sfml-system sfml-graphics sfml-window sfml-network)
