# have build directory be in different directory
if(PROJECT_SOURCE_DIR STREQUAL PROJECT_BINARY_DIR)
    message(
        FATAL_ERROR
        "In-source builds not allowed. Please make a 'build/' directory and run 'cmake ../' from there."
    )
endif()

# set build type if none specified
if (NOT CMAKE_BUILD_TYPE)
    message(STATUS "Setting build type to 'Debug' as none was specified.")
    set(CMAKE_BUILD_TYPE Debug CACHE STRING "Choose the type of build." FORCE)
    set_property(CACHE CMAKE_BUILD_TYPE
        PROPERTY STRINGS
        "Debug"
        "Release"
        "MinSizeRel"
        "RelWithDebInfo")
endif()

# set executable directory as build/bin
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin PARENT_SCOPE)

# export compile_commands.json for clang based tools like clangd
set(CMAKE_EXPORT_COMPILE_COMMANDS ON PARENT_SCOPE)

if(CMAKE_CXX_COMPILER_ID MATCHES ".*Clang")
    add_compile_options(-fcolor-diagnostics)
elseif(CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
    add_compile_options(-fdiagnostics-color=always)
endif()

# enable compiler cache (try sccache first then ccache)
# you can set CACHE_PROGRAMS like this: set(CACHE_PROGRAMS ccache mycache)
# to override the default cache program and their order of checking
if(NOT DEFINED CACHE_OPTIONS)
    set(CACHE_OPTIONS sccache ccache)
endif()

foreach(CACHE_OPTION ${CACHE_OPTIONS})
    find_program(CACHE_BINARY ${CACHE_OPTION})
    if(CACHE_BINARY)
        message(STATUS "Found ${CACHE_OPTION} and enabled.")
        set_property(GLOBAL PROPERTY RULE_LAUNCH_COMPILE ${CACHE_BINARY})
        break()
    endif()
endforeach()

# nice strict warnings
set(MSVC_WARNINGS
    /W4 # Baseline reasonable warnings
    /w14242 # 'identifier': conversion from 'type1' to 'type1', possible loss of data
    /w14254 # 'operator': conversion from 'type1:field_bits' to 'type2:field_bits', possible loss of data
    /w14263 # 'function': member function does not override any base class virtual member function
    /w14265 # 'classname': class has virtual functions, but destructor is not virtual instances of this class may not
            # be destructed correctly
    /w14287 # 'operator': unsigned/negative constant mismatch
    /we4289 # nonstandard extension used: 'variable': loop control variable declared in the for-loop is used outside
            # the for-loop scope
    /w14296 # 'operator': expression is always 'boolean_value'
    /w14311 # 'variable': pointer truncation from 'type1' to 'type2'
    /w14545 # expression before comma evaluates to a function which is missing an argument list
    /w14546 # function call before comma missing argument list
    /w14547 # 'operator': operator before comma has no effect; expected operator with side-effect
    /w14549 # 'operator': operator before comma has no effect; did you intend 'operator'?
    /w14555 # expression has no effect; expected expression with side- effect
    /w14619 # pragma warning: there is no warning number 'number'
    /w14640 # Enable warning on thread un-safe static member initialization
    /w14826 # Conversion from 'type1' to 'type_2' is sign-extended. This may cause unexpected runtime behavior.
    /w14905 # wide string literal cast to 'LPSTR'
    /w14906 # string literal cast to 'LPWSTR'
    /w14928 # illegal copy-initialization; more than one user-defined conversion has been implicitly applied
    /permissive- # standards conformance mode for MSVC compiler.
)

set(CLANG_WARNINGS
    -Wall
    -Wextra # reasonable and standard
    -Wshadow # warn the user if a variable declaration shadows one from a parent context
    -Wnon-virtual-dtor # warn the user if a class with virtual functions has a non-virtual destructor. This helps
                        # catch hard to track down memory errors
    -Wold-style-cast # warn for c-style casts
    -Wcast-align # warn for potential performance problem casts
    -Wunused # warn on anything being unused
    -Woverloaded-virtual # warn if you overload (not override) a virtual function
    -Wpedantic # warn if non-standard C++ is used
    -Wconversion # warn on type conversions that may lose data
    -Wsign-conversion # warn on sign conversions
    -Wnull-dereference # warn if a null dereference is detected
    -Wdouble-promotion # warn if float is implicit promoted to double
    -Wformat=2 # warn on security issues around functions that format output (ie printf)
)

set(GCC_WARNINGS
    ${CLANG_WARNINGS}
    -Wmisleading-indentation # warn if indentation implies blocks where blocks do not exist
    -Wduplicated-cond # warn if if / else chain has duplicated conditions
    -Wduplicated-branches # warn if if / else branches have duplicated code
    -Wlogical-op # warn about logical operations being used where bitwise were probably wanted
    -Wuseless-cast # warn if you perform a cast to the same type
)

if(MSVC)
    set(YACPM_WARNINGS ${MSVC_WARNINGS} CACHE STRING "Warnings set by yacpm_target_warnings")
elseif(CMAKE_CXX_COMPILER_ID MATCHES ".*Clang")
    set(YACPM_WARNINGS ${CLANG_WARNINGS} CACHE STRING "Warnings set by yacpm_target_warnings")
elseif(CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
    set(YACPM_WARNINGS ${GCC_WARNINGS} CACHE STRING "Warnings set by yacpm_target_warnings")
else()
    message(AUTHOR_WARNING "No compiler warnings set for '${CMAKE_CXX_COMPILER_ID}' compiler.")
endif()

# set strict warnings for a target
function(yacpm_target_warnings)
    list(GET ARGV -1 VISIBILITY)
    if(VISIBILITY STREQUAL "INTERFACE" OR VISIBILITY STREQUAL "PRIVATE" OR VISIBILITY STREQUAL "PUBLIC")
        list(REMOVE_AT ARGV -1)
    else()
        set(VISIBILITY PRIVATE)
    endif()
    foreach(TARGET ${ARGV})
        target_compile_options(${TARGET} ${VISIBILITY} ${YACPM_WARNINGS})
    endforeach()
endfunction()
