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

In your project directory create a `yacpm.json` file and add the required
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

Now add this to your top level CMakeLists.txt:

```cmake
if(NOT EXISTS "${CMAKE_BINARY_DIR}/yacpm.cmake")
    file(DOWNLOAD "https://github.com/Calbabreaker/yacpm/raw/v1/yacpm.cmake" "${CMAKE_BINARY_DIR}/yacpm.cmake")
endif()

include(${CMAKE_BINARY_DIR}/yacpm.cmake)
```

Now use the library in your project (all libraries names are kebab-case) as a
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

If the library doesn't exist in the remote(s) then specify a repository and a
cmake lists file (relative to yacpm.json file) for that library like so:

```json
{
    "packages": {
        "weird-library": {
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
directory](./packages)) to download from by setting remote in `yacpm.json`:

```json
{
    "remote": "https://example.com/packages"
}
```

## Adding a new package
