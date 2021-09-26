file(GLOB_RECURSE SPDLOG_SOURCES repository/src/*.cpp repository/include/*.h)
add_library(spdlog ${SPDLOG_SOURCES})

target_include_directories(spdlog SYSTEM PUBLIC repository/include)
target_compile_definitions(spdlog PRIVATE SPDLOG_COMPILED_LIB)
