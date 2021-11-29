file(GLOB_RECURSE AURORA_SOURCES repository/include/*.hpp)
add_library(aurora ${AURORA_SOURCES})

set_target_properties(aurora PROPERTIES LINKER_LANGUAGE CXX)
target_include_directories(aurora SYSTEM PUBLIC repository/include)
