set(YACPM_BRANCH "main")

if(NOT EXISTS "${CMAKE_CURRENT_BINARY_DIR}/yacpm.py")
    message(STATUS "Downloading yacpm.py on ${YACPM_BRANCH}...")
    file(DOWNLOAD "https://github.com/Calbabreaker/yacpm/raw/${YACPM_BRANCH}/yacpm.py" "${CMAKE_CURRENT_BINARY_DIR}/yacpm.py")
endif()

function(watch_file file)
    if(EXISTS ${file})
        configure_file(${file} ${file} COPYONLY)
    endif()
endfunction()

watch_file(${CMAKE_CURRENT_SOURCE_DIR}/yacpkgs/CMakeLists.txt)
watch_file(${CMAKE_CURRENT_SOURCE_DIR}/yacpm.json)

execute_process(
    COMMAND python ${CMAKE_CURRENT_BINARY_DIR}/yacpm.py
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
    RESULT_VARIABLE result
)

if(result)
    message(FATAL_ERROR "Failed to run yacpm.py!")
endif()

include(${CMAKE_CURRENT_SOURCE_DIR}/yacpkgs/packages.cmake)
