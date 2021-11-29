file(GLOB_RECURSE THOR_SOURCES repository/include/*.hpp)
add_library(thor ${THOR_SOURCES})

set_target_properties(thor PROPERTIES LINKER_LANGUAGE CXX)
target_include_directories(thor SYSTEM PUBLIC repository/include)