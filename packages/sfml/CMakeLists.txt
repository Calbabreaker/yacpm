project(SFML)
set(PROJECT_SOURCE_DIR ${CMAKE_CURRENT_SOURCE_DIR}/repository)

include(repository/cmake/Config.cmake)
add_subdirectory(repository/src/SFML)

file(GLOB_RECURSE SFML_SOURCES repository/include/SFML/*.hpp)
add_library(sfml ${SFML_SOURCES})

target_include_directories(sfml-system SYSTEM PUBLIC repository/include)
target_link_libraries(sfml sfml-graphics sfml-audio sfml-system sfml-graphics sfml-window sfml-network)
set_target_properties(sfml PROPERTIES LINKER_LANGUAGE CXX)
