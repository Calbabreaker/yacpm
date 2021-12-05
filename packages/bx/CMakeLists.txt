file(GLOB_RECURSE BX_SOURCES repository/src/*.cpp repository/include/*.h)
add_library(bx STATIC ${BX_SOURCES})

# Link against psapi on Windows
if(WIN32)
	target_link_libraries(bx PUBLIC psapi)
endif()

target_include_directories(bx PUBLIC SYSTEM repository/include repository/3rdparty)

# Build system specific configurations
if(MINGW)
    target_include_directories(bx PUBLIC SYSTEM repository/include/compat/mingw)
elseif(WIN32)
    target_include_directories(bx PUBLIC SYSTEM repository/include/compat/msvc)
elseif(APPLE)
    target_include_directories(bx PUBLIC SYSTEM repository/include/compat/osx)
endif()

# All configurations
target_compile_definitions(bx PUBLIC "__STDC_LIMIT_MACROS")
target_compile_definitions(bx PUBLIC "__STDC_FORMAT_MACROS")
target_compile_definitions(bx PUBLIC "__STDC_CONSTANT_MACROS")
if (DEFINED BX_CONFIG_DEBUG)
    target_compile_definitions(bx PUBLIC "BX_CONFIG_DEBUG=${BX_CONFIG_DEBUG}")
else()
    if(CMAKE_BUILD_TYPE STREQUAL "Debug")
        target_compile_definitions(bx PUBLIC "BX_CONFIG_DEBUG=1")
    else()
        target_compile_definitions(bx PUBLIC "BX_CONFIG_DEBUG=0")
    endif()
endif()

# Additional dependencies on Unix
if(UNIX AND NOT APPLE AND NOT ANDROID)
	# Threads
	find_package(Threads)
	target_link_libraries(bx ${CMAKE_THREAD_LIBS_INIT} dl)

	# Real time (for clock_gettime)
	target_link_libraries(bx rt)
elseif(APPLE)
	find_library(FOUNDATION_LIBRARY Foundation)
	mark_as_advanced(FOUNDATION_LIBRARY)
	target_link_libraries(bx PUBLIC ${FOUNDATION_LIBRARY})
endif()
