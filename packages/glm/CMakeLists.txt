file(GLOB_RECURSE GLM_SOURCES repository/glm/*.cpp repository/glm/*.inl repository/glm/*.hpp)
add_library(glm ${GLM_SOURCES})

target_include_directories(glm SYSTEM PUBLIC repository)
