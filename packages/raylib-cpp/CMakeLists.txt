include(repository/yacpkgs/packages.cmake)
add_library(raylib-cpp INTERFACE)
target_include_directories(raylib-cpp SYSTEM INTERFACE repository/include)
target_link_libraries(raylib-cpp INTERFACE raylib)
