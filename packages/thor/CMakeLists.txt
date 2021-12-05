file(GLOB_RECURSE THOR_SOURCES repository/include/*.hpp repository/src/*.cpp)
add_library(thor ${THOR_SOURCES})

if(TARGET aurora)
    target_link_libraries(thor PUBLIC aurora)
else()
    target_include_directories(thor SYSTEM PUBLIC repository/include repository/extlibs/aurora/include)
endif()
