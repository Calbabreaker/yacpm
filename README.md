# Yet Another C/C++ Package Manager

Easy to use, fast, git sourced based, C/C++ package manager.

## Features

-   No need to install a program, just include the cmake file
-   Can specify other libraries not in default package remote
-   Package code is in project directory making it easily accessible
-   Only fetches required files (using git sparse-checkout) which takes
    less time and bandwidth to get packages (unlike git submodules)

## Requirements

-   Python >= 3.6
-   Cmake >= 3.12
-   Git >= 2.27

## Usage

See [example](./example/) for a full example.

In the project directory create a `yacpm.json` file and add the required
packages in there in the `packages` field as an object with the key being the
library name and value being the version (commit hash/tag/branch of repository)
or an object having the version field:

```json
{
    "packages": {
        "glfw": "3.3.4",
        "entt": "master",
        "imgui": {
            "version": "c58fb464113435fdb7d122fde87cef4920b3d2c6"
        }
    }
}
```

If a branch is specified, it will be automatically converted to a commit hash
(to prevent code from suddenly breaking) unless there's a + at the front. For
example, `master` will be converted to
`3f786850e387550fdab836ed7e6dc881de23001b` but not `+master`. If no version is
specified at all (empty string), it will use the default branch of the
repository which will then be converted a commit and saved to yacpm.json. Using
`+` will use the default branch and saved to yacpm.json (unless `++` is used)
but it will not convert it to a commit.

Now add this to the top level CMakeLists.txt:

```cmake
if(NOT EXISTS "${CMAKE_BINARY_DIR}/yacpm.cmake")
    # uses v1 of yacpm, replace the v1 with v2, v3, etc. to use a different version. See https://github.com/Calbabreaker/yacpm#branches
    file(DOWNLOAD "https://github.com/Calbabreaker/yacpm/raw/v1/yacpm.cmake" "${CMAKE_BINARY_DIR}/yacpm.cmake")
endif()

include(${CMAKE_BINARY_DIR}/yacpm.cmake)
```

Now use the library in the project (all libraries names are snake_case) as a
target (include directories are automatically set):

```cmake
# all of them in yacpm.json
target_link_libraries(${PROJECT_NAME} ${YACPM_PKGS})

# only specific ones
target_link_libraries(${PROJECT_NAME} glfw imgui)
```

Then run cmake:

```sh
mkdir build
cd build
cmake ..
```

Yacpm will download the `yacpkg.json` file for the library, the files and
directories specified in `yacpkg.json` and the necessary `CMakeLists.txt`
putting it all into a directory named the package name in the `yacpkgs`
directory.

You can also include or disinclude other folders (array or string) to be
fetched (in gitignore syntax):

```json
{
    "packages": {
        "imgui": {
            "version": "docking",
            "include": ["/backends", "!/backends/imgui_impl_dx9.*"]
        }
    }
}
```

If the library doesn't exist in the remote then specify a repository and a
CMakeLists.txt (file relative to yacpm.json or a url) that makes a target with
the name matching the package name for that library like so:

```json
{
    "packages": {
        "weird-library": {
            "version": "c8fed00eb2e87f1cee8e90ebbe870c190ac3848c",
            "repository": "https://github.com/RandomUser/weird-library",
            "cmake": "lib/weird-library.cmake",
            "include": ["/src", "/include"]
        }
    }
}
```

You can also configure the package by setting cmake variables (uses CACHE FORCE)
by having a variables object like this (this is how you configure glad):

```json
{
    "packages": {
        "glad": {
            "version": "71b2aa61f1f0ae94be5f2a7674275966aa15f8ad",
            "variables": { "GLAD_PROFILE": "core", "GLAD_API": "gl=3.2" }
        }
    }
}
```

Setting `BUILD_SHARED_LIBS` variable to true will link the library dynamically
or setting it globally will link all the libraries libraries dynamically. Note
you might have to remove `build/CMakeCache.txt` in order for it to actually
work.

There might also be a README.md in the packages remote directory that contains
notes on the package.

## Additional Options

You can log everything by setting verbose to true in `yacpm.json`:

```json
{
    "verbose": true
}
```

You can set a different package repository (default is [packages](./packages))
as either a url or local directory to download from by setting remote in
`yacpm.json`. This can be an array or string (yacpm will try to use first ones
first) and DEFAULT_REMOTE can be use as alias to the default remote:

```json
{
    "remote": ["https://example.com/packages", "./packages", "DEFAULT_REMOTE"]
}
```

There is also a [yacpm_extended.cmake](./yacpm_extended.cmake) file that
contains nice cmake utilities that you can use by doing:

```cmake
include(${CMAKE_BINARY_DIR}/yacpm.cmake)
yacpm_use_extended() # run after including yacpm.cmake
```

This contains a `yacpm_target_warnings(target visibility)` function that takes in a
target and a visibility (PUBLIC, PRIVATE, INTERFACE) and sets strict warnings
for that target. It also enables [ccache](https://ccache.dev/) or
[sccache](https://github.com/mozilla/sccache), exports
`compile_commands.json` (for language servers), and puts executables into
`build/bin`.

## Testing

Run the [run_tests.py](./tests/run_test.py) to run tests in the
[tests](./tests) folder (specified by cli args) or all of them by default.
Run `python3 tests/run_test.py -h` for more information. This will also be ran
with github-actions. Each tests are like integration tests that tests features
in yacpm to make sure nothing breaks for users.

## Adding a new package

Create a new directory in [packages](./packages) directory with the name being
the package name. This name **must** be in snake_case. Make a `yacpkg.json`
file with the repository of the package and directories to fetch from the repository. The
repository can be any git repository but it has to support sparse-checkout and
filter fetches which github does. Set the yacpm field to a yacpm config file to
get any packages that are needed for that package.

```json
{
    "repository": "https://github.com/bkaradzic/bgfx",
    "include": ["/3rdparty/webgpu", "/include", "/src"],
    "yacpm": {
        "packages": { "bimg": "" }
    }
}
```

Now make a `CMakeLists.txt` in that directory. The file should be versatile as
possible (work on as many versions) meaning add_subdirectory should be used
(unless it's simple like glm) and all files should be globed. If the library
target name is not in snake_case, do `add_library(library_name ALIAS LibaryName)`.
It doesn't have to work on very old versions, just at least 2
years. Also use system headers for include directories to avoid compiler
warnings from the library header.

#### Example for GLFW:

```cmake
set(GLFW_BUILD_DOCS OFF CACHE BOOL "" FORCE)
set(GLFW_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
set(GLFW_BUILD_TESTS OFF CACHE BOOL "" FORCE)
set(GLFW_INSTALL OFF CACHE BOOL "" FORCE)

add_subdirectory(repository)
```

#### Example for spdlog:

```cmake
file(GLOB_RECURSE SPDLOG_SOURCES repository/src/*.cpp repository/include/*.h)
add_library(spdlog ${SPDLOG_SOURCES})

# system headers like this
target_include_directories(spdlog SYSTEM PUBLIC repository/include)
target_compile_definitions(spdlog PRIVATE SPDLOG_COMPILED_LIB)
```

Now add the package to
[tests/all_packages/yacpm.json](./tests/all_packages/yacpm.json) to test if the
package was configured correctly. Put package the package in
[tests/all_packages_other/yacpm.json](./tests/all_packages_other/yacpm.json) if
the package conflicts with other ones in yacpm. Then include the package header
file and function call that's statically linked (if not package is not header
only) in the corresponding main.cpp file. Make sure the package in yacpm.json
and function call is in alphabetical order.

After everything has been tested, submit a pull request to the main branch to
have the package be in the default remote.

## Branches

The main branch contains the most recent commits where the latest potentially
breaking changes come in so it shouldn't be used. The vN (v1, v2, etc.)
branches are stable and should be used. Every time there is change that is
incompatible with previous yacpm.json specifications the version number will be
incremented.
