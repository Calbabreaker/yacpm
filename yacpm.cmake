set(YACPM_BRANCH "v1")

# sets (do not touch lines above or merge conflict will happen)
set(BUILD_SHARED_LIBS FALSE)

function(download_file FILE_NAME FILE_EXTENSION)
    # append -$YACPM_BRANCH to filename to have multiple packages using yacpm without duplication issues
    set(FILE "${FILE_NAME}-${YACPM_BRANCH}.${FILE_EXTENSION}")
    if(NOT EXISTS "${CMAKE_BINARY_DIR}/${FILE}")
        message(STATUS "Downloading ${FILE}...")
        file(DOWNLOAD "https://github.com/Calbabreaker/yacpm/raw/${YACPM_BRANCH}/${FILE_NAME}.${FILE_EXTENSION}" "${CMAKE_BINARY_DIR}/${FILE}")
    endif()
    set(FILE ${FILE} PARENT_SCOPE)
endfunction()

function(watch_file FILE)
    if(EXISTS ${FILE})
        configure_file(${FILE} ${FILE} COPYONLY)
    endif()
endfunction()

download_file("yacpm" "py")
set(YACPM_PY ${FILE}) # download_file sets the FILE variable globally

watch_file(${CMAKE_CURRENT_SOURCE_DIR}/yacpkgs/packages.cmake) # force rerun configure if yacpkgs is deleted
watch_file(${CMAKE_CURRENT_SOURCE_DIR}/yacpm.json) # force rerun configure if yacpm.json changes

message(STATUS "Running ${YACPM_PY} for ${PROJECT_NAME}")
execute_process(
    COMMAND python3 ${CMAKE_BINARY_DIR}/${YACPM_PY}
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
    RESULT_VARIABLE RESULT_CODE
)

if(RESULT_CODE)
    message(FATAL_ERROR "Failed to run ${YACPM_PY} for ${PROJECT_NAME}!")
endif()

include(${CMAKE_CURRENT_SOURCE_DIR}/yacpkgs/packages.cmake)

# run this function to use the yacpm_extended.cmake which contains nice things 
function(yacpm_use_extended)
    download_file("yacpm_extended" "cmake")
    include("${CMAKE_BINARY_DIR}/${FILE}")
endfunction()
