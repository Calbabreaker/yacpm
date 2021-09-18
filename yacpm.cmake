set(YACPM_BRANCH "main")

if(NOT EXISTS "${CMAKE_BINARY_DIR}/yacpm.py")
    message(STATUS "Downloading yacpm.py on ${YACPM_BRANCH}...")
    file(DOWNLOAD "https://github.com/Calbabreaker/yacpm/raw/${YACPM_BRANCH}/yacpm.py" "${CMAKE_BINARY_DIR}/yacpm.py")
endif()

add_custom_command(
    OUTPUT yacpm_packages PRE_BUILD
    COMMAND python ${CMAKE_BINARY_DIR}/yacpm.py
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
    DEPENDS ${CMAKE_SOURCE_DIR}/yacpm.json
)

add_custom_target(
    yacpm
    ALL
    DEPENDS yacpm_packages
)
