project(STB LANGUAGES C)

file(GLOB STB_SOURCES repository/*.h)
add_library(stb ${STB_SOURCES})

set_target_properties(stb PROPERTIES LINKER_LANGUAGE C)
target_include_directories(stb PUBLIC repository)
