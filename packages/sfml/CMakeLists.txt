project(SFML)
set(PROJECT_SOURCE_DIR ${CMAKE_CURRENT_SOURCE_DIR}/repository)

include(repository/cmake/Config.cmake)
add_subdirectory(repository/)

file(GLOB_RECURSE SFML_SOURCES repository/include/SFML/*.hpp)
add_library(sfml ${SFML_SOURCES})

target_include_directories(sfml SYSTEM PUBLIC repository/include/)
set_target_properties(sfml PROPERTIES LINKER_LANGUAGE CXX)
target_link_libraries(sfml 
    $<TARGET_NAME_IF_EXISTS:sfml-audio> 
    $<TARGET_NAME_IF_EXISTS:sfml-system> 
    $<TARGET_NAME_IF_EXISTS:sfml-graphics> 
    $<TARGET_NAME_IF_EXISTS:sfml-window> 
    $<TARGET_NAME_IF_EXISTS:sfml-network>
)
