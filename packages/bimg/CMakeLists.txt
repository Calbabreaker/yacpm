include(repository/yacpkgs/packages.cmake)

# Third party libs
function(add_3rdparty TARGET_NAME)
    file(GLOB_RECURSE LIB_SOURCES 
        repository/3rdparty/${TARGET_NAME}/*.cpp 
        repository/3rdparty/${TARGET_NAME}/*.cc 
        repository/3rdparty/${TARGET_NAME}/*.c 
        repository/3rdparty/${TARGET_NAME}/*.h 
        repository/3rdparty/${TARGET_NAME}/*.inl)
    add_library(${TARGET_NAME} STATIC ${LIB_SOURCES})
endfunction()

set(3RD_PARTY_LIBRARIES astc-codec astc edtaa3 etc1 etc2 iqa libsquish nvtt pvrtc tinyexr)
foreach(TARGET_NAME IN ITEMS astc-codec astc edtaa3 etc1 etc2 iqa libsquish nvtt pvrtc tinyexr)
    add_3rdparty(${TARGET_NAME})
endforeach()

target_include_directories(astc-codec PUBLIC SYSTEM repository/3rdparty/astc-codec repository/3rdparty/astc-codec/include)
target_include_directories(nvtt PUBLIC SYSTEM repository/3rdparty/nvtt)
target_include_directories(tinyexr PUBLIC SYSTEM repository/3rdparty/tinyexr/deps/miniz)
target_include_directories(iqa PUBLIC SYSTEM repository/3rdparty/iqa/include)
target_link_libraries(nvtt PRIVATE bx)
target_link_libraries(etc2 PRIVATE bx)

file(GLOB_RECURSE BIMG_SOURCES repository/src/*.cpp repository/include/*.h)
add_library(bimg ${BIMG_SOURCES})
target_include_directories(bimg PUBLIC SYSTEM repository/include repository/3rdparty)
target_link_libraries(bimg bx ${3RD_PARTY_LIBRARIES})
