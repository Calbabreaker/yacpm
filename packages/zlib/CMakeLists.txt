file(GLOB ZLIB_SOURCES repository/*.c repository/*.h)
add_library(zlib ${ZLIB_SOURCES})

target_include_directories(zlib SYSTEM PUBLIC repository)
