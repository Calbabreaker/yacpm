set(YACPM_BRANCH "main")

# sets (do not touch lines above or merge conflict will happen)
if(NOT DEFINED BUILD_SHARED_LIBS)
    set(BUILD_SHARED_LIBS FALSE)
endif()

function(download_file FILE_NAME)
    if(NOT EXISTS ${CMAKE_BINARY_DIR}/${FILE_NAME})
        message(STATUS "Downloading ${FILE_NAME}...")
        file(DOWNLOAD https://github.com/Calbabreaker/yacpm/raw/${YACPM_BRANCH}/${FILE_NAME} ${CMAKE_BINARY_DIR}/${FILE_NAME})
    endif()
endfunction()

function(watch_file FILE)
    if(EXISTS ${FILE})
        configure_file(${FILE} ${FILE} COPYONLY)
    endif()
endfunction()

# run this function to use the yacpm_extended.cmake which contains nice things 
function(yacpm_use_extended)
    download_file(yacpm_extended.cmake)
    include(${CMAKE_BINARY_DIR}/yacpm_extended.cmake)
endfunction()

# only do if is top level yacpm or if the top level yacpm.json doesn't exist
# in order to handle multiple packages using the same package
if(CMAKE_CURRENT_SOURCE_DIR STREQUAL CMAKE_SOURCE_DIR OR NOT EXISTS ${CMAKE_SOURCE_DIR}/yacpm.json)
    watch_file(${CMAKE_CURRENT_SOURCE_DIR}/yacpkgs/packages.cmake)
    watch_file(${CMAKE_CURRENT_SOURCE_DIR}/yacpm.json) # force rerun configure if yacpm.json changes

    download_file(yacpm.py)

    # find correct python executable
    find_package(Python3 COMPONENTS Interpreter REQUIRED)
    message(STATUS "Running yacpm.py for ${PROJECT_NAME}")
    execute_process(
        COMMAND ${Python3_EXECUTABLE} ${CMAKE_BINARY_DIR}/yacpm.py
        WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
        RESULT_VARIABLE RESULT_CODE
    )

    if(RESULT_CODE)
        message(FATAL_ERROR "Failed to run yacpm.py for ${PROJECT_NAME}!")
    endif()
endif()

include(${CMAKE_CURRENT_SOURCE_DIR}/yacpkgs/packages.cmake)
