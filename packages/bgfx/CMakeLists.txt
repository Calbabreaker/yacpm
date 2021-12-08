include(repository/yacpkgs/packages.cmake)

set(BGFX_OPENGL_VERSION "" CACHE STRING "Specify minimum opengl version")
set(BGFX_OPENGLES_VERSION "" CACHE STRING "Specify minimum OpenGL ES version")
option(BGFX_BUILD_COMPILERS "Build shaderc and geometryc" OFF)

file(GLOB_RECURSE BGFX_SOURCES repository/src/*.cpp repository/src/*.mm repository/src/*.h repository/include/*.h)
add_library(bgfx ${BGFX_SOURCES})

if (EMSCRIPTEN)
    target_compile_definitions(bgfx PRIVATE BGFX_CONFIG_RENDERER_WEBGPU=1)
    target_link_options(bgfx PRIVATE "-s USE_WEBGPU=1")
endif()

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
    SYSTEM PUBLIC
		repository/3rdparty
		repository/3rdparty/dxsdk/include
		repository/3rdparty/khronos
		repository/include)

target_link_libraries(bgfx PUBLIC bimg)

# Frameworks required on iOS, tvOS and macOS
if(CMAKE_SYSTEM_NAME MATCHES iOS|tvOS)
	target_link_libraries(bgfx PUBLIC "-framework OpenGLES -framework Metal -framework UIKit -framework CoreGraphics -framework QuartzCore")
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

macro(add_3rdparty LIBRARY_NAME)
    if(IS_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/repository/3rdparty/${LIBRARY_NAME})
        cmake_parse_arguments(LIBRARY "" "" "GLOB;INCLUDE;DEFINITIONS" ${ARGN})
        list(TRANSFORM LIBRARY_GLOB PREPEND "repository/3rdparty/${LIBRARY_NAME}/")
        file(GLOB_RECURSE LIBRARY_SOURCES ${LIBRARY_GLOB})
        add_library(${LIBRARY_NAME} STATIC ${LIBRARY_SOURCES})

        if(DEFINED LIBRARY_INCLUDE)
            list(TRANSFORM LIBRARY_INCLUDE PREPEND "repository/3rdparty/${LIBRARY_NAME}/")
            target_include_directories(${LIBRARY_NAME} SYSTEM PUBLIC ${LIBRARY_INCLUDE})
        endif()
        if(DEFINED LIBRARY_DEFINITIONS)
            target_compile_definitions(${LIBRARY_NAME} PRIVATE ${LIBRARY_DEFINITIONS})
        endif()
    endif()
endmacro()

# build bgfx tools
if(BGFX_BUILD_COMPILERS)
    add_3rdparty(fcpp GLOB *.c *.h INCLUDE / DEFINITIONS NINCLUDE=64 NWORK=65536 NBUFF=65536 OLD_PREPROCESSOR=0)
    add_3rdparty(glsl-optimizer GLOB *.c *.cpp *.h INCLUDE include src src/mesa src/mapi src/glsl)
    add_3rdparty(glslang 
        DEFINITIONS ENABLE_OPT=1 ENABLE_HLSL=1
        GLOB hlsl/*.cpp SPIRV/*.cpp OGLCompilersDLL/*.cpp glslang/GenericCodeGen/*.cpp glslang/MachineIndependent/*.cpp glslang/HLSL/*.cpp
        INCLUDE ../ / glslang/Include glslang/Public)
    add_3rdparty(meshoptimizer GLOB src/*.cpp src/*.h)
    add_3rdparty(spirv-cross GLOB *.cpp *.h INCLUDE include / DEFINITIONS SPIRV_CROSS_EXCEPTIONS_TO_ASSERTIONS)
    add_3rdparty(spirv-tools GLOB *.cpp *.h INCLUDE / include ../spirv-headers/include source include/generated)

    target_link_libraries(glslang PUBLIC spirv-tools)

    if(WIN32)
        target_sources(glslang PRIVATE repository/3rdparty/glslang/glslang/OSDependent/Windows/ossource.cpp)
    else()
        target_sources(glslang PRIVATE repository/3rdparty/glslang/glslang/OSDependent/Unix/ossource.cpp)
    endif()

    add_executable(geometryc repository/tools/geometryc/geometryc.cpp)
    target_link_libraries(geometryc PRIVATE bx bgfx meshoptimizer)

    file(GLOB SHADERC_SOURCES repository/tools/shaderc/*.cpp repository/tools/shaderc/*.h)
    add_executable(shaderc ${SHADERC_SOURCES})
    target_link_libraries(shaderc PRIVATE bx bimg bgfx fcpp glsl-optimizer glslang spirv-cross)
    target_include_directories(shaderc PRIVATE repository/3rdparty/webgpu/include)
endif()
