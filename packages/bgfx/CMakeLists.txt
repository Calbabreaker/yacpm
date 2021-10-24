include(repository/yacpkgs/packages.cmake)

set(BGFX_OPENGL_VERSION "" CACHE STRING "Specify minimum opengl version")
set(BGFX_OPENGLES_VERSION "" CACHE STRING "Specify minimum OpenGL ES version")
option(BGFX_CONFIG_RENDERER_WEBGPU "Enables the webgpu renderer" OFF)

if(NOT APPLE)
	set(BGFX_AMALGAMATED_SOURCE repository/src/amalgamated.cpp)
else()
	set(BGFX_AMALGAMATED_SOURCE repository/src/amalgamated.mm)
endif()

# Grab the bgfx source files
file(GLOB_RECURSE BGFX_SOURCES repository/src/*.cpp repository/src/*.mm repository/src/*.h repository/include/*.h)
set(BGFX_NOBUILD ${BGFX_SOURCES})
list(REMOVE_ITEM BGFX_NOBUILD ${BGFX_AMALGAMATED_SOURCE})
foreach(BGFX_SRC ${BGFX_NOBUILD})
    set_source_files_properties(${BGFX_SRC} PROPERTIES HEADER_FILE_ONLY ON)
endforeach()

# Create the bgfx target
add_library(bgfx ${BGFX_SOURCES})

if(BGFX_CONFIG_RENDERER_WEBGPU)
    file(
        GLOB
        WEBGPU_SOURCES
        repository/3rdparty/webgpu/include/webgpu/*.h
        repository/3rdparty/webgpu/webgpu_cpp.cpp  # requires dawn to be installed
    )

    add_library(webgpu STATIC ${WEBGPU_SOURCES})
    target_include_directories(webgpu PUBLIC repository/3rdparty/webgpu/include)
    target_compile_definitions(bgfx PRIVATE BGFX_CONFIG_RENDERER_WEBGPU=1)
    if (EMSCRIPTEN)
        target_link_options(bgfx PRIVATE "-s USE_WEBGPU=1")
    else()
        target_link_libraries(bgfx PRIVATE webgpu)
    endif()
endif()

# Enable BGFX_CONFIG_DEBUG in Debug configuration
target_compile_definitions(bgfx PRIVATE "$<$<CONFIG:Debug>:BGFX_CONFIG_DEBUG=1>")

if(NOT ${BGFX_OPENGL_VERSION} STREQUAL "")
	target_compile_definitions(bgfx PRIVATE BGFX_CONFIG_RENDERER_OPENGL_MIN_VERSION=${BGFX_OPENGL_VERSION})
endif()

if(NOT ${BGFX_OPENGLES_VERSION} STREQUAL "")
	target_compile_definitions(bgfx PRIVATE BGFX_CONFIG_RENDERER_OPENGLES_MIN_VERSION=${BGFX_OPENGLES_VERSION})
endif()

# Special Visual Studio Flags
if(MSVC)
	target_compile_definitions(bgfx PRIVATE "_CRT_SECURE_NO_WARNINGS")
endif()

# Includes
target_include_directories(bgfx
	PRIVATE
		repository/3rdparty
		repository/3rdparty/dxsdk/include
		repository/3rdparty/khronos
	PUBLIC
		repository/include)

target_link_libraries(bgfx bimg)

# Frameworks required on iOS, tvOS and macOS
if(${CMAKE_SYSTEM_NAME} MATCHES iOS|tvOS)
	target_link_libraries (bgfx PUBLIC "-framework OpenGLES  -framework Metal -framework UIKit -framework CoreGraphics -framework QuartzCore")
elseif(APPLE)
	find_library(COCOA_LIBRARY Cocoa)
	find_library(METAL_LIBRARY Metal)
	find_library(QUARTZCORE_LIBRARY QuartzCore)
	mark_as_advanced(COCOA_LIBRARY)
	mark_as_advanced(METAL_LIBRARY)
	mark_as_advanced(QUARTZCORE_LIBRARY)
	target_link_libraries(bgfx PUBLIC ${COCOA_LIBRARY} ${METAL_LIBRARY} ${QUARTZCORE_LIBRARY})
endif()

if(UNIX AND NOT APPLE AND NOT EMSCRIPTEN AND NOT ANDROID)
	find_package(X11 REQUIRED)
	find_package(OpenGL REQUIRED)
	target_link_libraries(bgfx PUBLIC ${X11_LIBRARIES} ${OPENGL_LIBRARIES})
endif()

# Exclude mm files if not on OS X
if(NOT APPLE)
	set_source_files_properties(repository/src/glcontext_eagl.mm PROPERTIES HEADER_FILE_ONLY ON)
	set_source_files_properties(repository/src/glcontext_nsgl.mm PROPERTIES HEADER_FILE_ONLY ON)
	set_source_files_properties(repository/src/renderer_mtl.mm PROPERTIES HEADER_FILE_ONLY ON)
endif()

# Exclude glx context on non-unix
if(NOT UNIX OR APPLE)
	set_source_files_properties(repository/src/glcontext_glx.cpp PROPERTIES HEADER_FILE_ONLY ON)
endif()

# in Xcode we need to specify this file as objective-c++ (instead of renaming to .mm)
if (XCODE)
	set_source_files_properties(repository/src/renderer_vk.cpp PROPERTIES LANGUAGE OBJCXX XCODE_EXPLICIT_FILE_TYPE sourcecode.cpp.objcpp)
endif()
