# Yet Another C/C++ Package Manager

Easy to use, git sourced based, statically linked C/C++ package manager

## Features

-   No need to install a program; just include the cmake file
-   Only fetch required directories (using git sparse-checkout) unlike tradtitional git submodules
-   Library code is in project direcory so library code can be easily accessed
-   Can specify other libraries not found in default packages

## Requirements

-   Python >= 3.5
-   Cmake >= 3.12
-   Git >= 2.3

## Usage

In the project directory create a `yacpm.json` file and add the required
packages in there in the `packages` field as an object with the key being the
libary name and value being the version (commit hash/tag/branch of repository)
or an object having the version field:

```json
{
    "packages": {
        "glfw": "3.3.4",
        "entt": "57b0624a0ac4901d8fe1802f39e2b43e7f3ed114",
        "imgui": {
            "version": "c58fb464113435fdb7d122fde87cef4920b3d2c6"
        }
    }
}
```

It is recommended to not uses branches since the project can break suddenly if
there are any breaking changes to the branch.

Now add this to the top level CMakeLists.txt:

```cmake
if(NOT EXISTS "${CMAKE_BINARY_DIR}/yacpm.cmake")
    file(DOWNLOAD "https://github.com/Calbabreaker/yacpm/raw/v1/yacpm.cmake" "${CMAKE_BINARY_DIR}/yacpm.cmake")
endif()

include(${CMAKE_BINARY_DIR}/yacpm.cmake)
```

Now use the library in the project (all libraries names are snake_case) as a
target (include directories are automatically set):

```cmake
# all of them in yacpm.json
target_link_libraries(${PROJECT_NAME} ${YACPM_LIBS})

# only specific ones
target_link_libraries(${PROJECT_NAME} glfw imgui)
```

Then run cmake:

```sh
mkdir build
cmake ..
```

Yacpm will download the `yacpkg.json` file for the library, fetch the
repository top level files in the repo and other directories specified in
`yacpkg.json` and the necessery `CMakeLists.txt` putting it all into the
`yacpkgs` directory.

You can also include other folders (array or string) to be fetched (this uses
git's sparse checkout in cone mode):

```json
{
    "packages": {
        "imgui": {
            "version": "c58fb464113435fdb7d122fde87cef4920b3d2c6",
            "include": "backends"
        }
    }
}
```

If the library doesn't exist in the remote then specify a repository and a
cmake lists file (relative to yacpm.json file) for that library like so:

```json
{
    "packages": {
        "weird-library": {
            "version": "c8fed00eb2e87f1cee8e90ebbe870c190ac3848c",
            "repository": "https://github.com/RandomUser/weird-library",
            "cmake": "lib/weird-library.cmake",
            "include": ["src", "include"]
        }
    }
}
```

## Aditional Options

You can log everything by setting verbose to true in `yacpm.json`:

```json
{
    "verbose": true
}
```

You can set a different package repository (default is [packages
directory](./packages)) as either a url or local directory to download from by
setting remote in `yacpm.json`:

```json
{
    "remote": "https://example.com/packages"
}
```

## Adding a new package

Create a new directory in [packages](./packages) directory with the name being
the package name. Make a `yacpkg.json` file with the repository of the package
and aditional include directories.

```json
{
    "repository": "https://github.com/glfw/glfw/",
    "include": ["src", include"]
}
```

Now make a `CMakeLists.txt` in the directory. The file should be versatile as
possible (work on as many versions) meaning that any CMakeLists.txt in the
package should be used if there is one and all files should be globbed. The
library target name should also be in snake_case so renamming of targets might
need to happen.

Example for GLFW:

```cmake
set(GLFW_BUILD_DOCS OFF CACHE BOOL "" FORCE)
set(GLFW_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
set(GLFW_BUILD_TESTS OFF CACHE BOOL "" FORCE)
set(GLFW_INSTALL OFF CACHE BOOL "" FORCE)

add_subdirectory(repository)
```

Example for ImGui:

```cmake
file(GLOB IMGUI_SOURCES repository/*.cpp repository/*.h)
add_library(imgui ${IMGUI_SOURCES})

target_include_directories(imgui PUBLIC repository)
```

If the package had a massive change breaking the CMakeLists.txt or yacpkg.json
config, then specify a configs field with its field being the unix timestamp
of the breaking commit (find out using `git show -s --format=%ct {COMMIT}`).
Then have the cmake file (default is CMakeLists.txt), and aditional include
(will be combined with yacpkg.json include dirs) directories properties specified.
If version can't be supported at all set it to null.

Example for GLFW (lib was renamed to src):

```cmake
{
    "repository": "https://github.com/glfw/glfw/",
    "include": ["include"],
    "configs": {
        "0": { "include": ["lib"] },
        "1284055303": { "include": ["src"] },
    }
}
```

After everything has been tested, submit a pull request to have the package be
in the default remote.
