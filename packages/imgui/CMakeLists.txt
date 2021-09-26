file(GLOB IMGUI_SOURCES repository/*.cpp repository/*.h)
add_library(imgui ${IMGUI_SOURCES})

target_include_directories(imgui SYSTEM PUBLIC repository)
