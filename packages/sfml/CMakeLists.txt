add_subdirectory(repository)

add_library(sfml INTERFACE)
target_include_directories(sfml SYSTEM INTERFACE repository/include/)
target_link_libraries(sfml INTERFACE
    $<TARGET_NAME_IF_EXISTS:sfml-audio> 
    $<TARGET_NAME_IF_EXISTS:sfml-system> 
    $<TARGET_NAME_IF_EXISTS:sfml-graphics> 
    $<TARGET_NAME_IF_EXISTS:sfml-window> 
    $<TARGET_NAME_IF_EXISTS:sfml-network>
)
