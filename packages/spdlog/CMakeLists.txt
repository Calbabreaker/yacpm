find_package(Threads REQUIRED)

file(GLOB_RECURSE SPDLOG_SOURCES repository/src/*.cpp repository/include/*.h)
add_library(spdlog ${SPDLOG_SOURCES})

set_target_properties(spdlog PROPERTIES LINKER_LANGUAGE CXX)
target_include_directories(spdlog SYSTEM PUBLIC repository/include)
target_compile_definitions(spdlog PUBLIC SPDLOG_COMPILED_LIB)
target_link_libraries(spdlog PUBLIC Threads::Threads)
