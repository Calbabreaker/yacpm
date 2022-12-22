# Yet Another C/C++ Package Manager

Easy to use, fast, git sourced based, C/C++ package manager.

## Features

-   No need to install a program, just include the cmake file
-   Can specify other libraries not in default package remote
-   Package code is in project directory making it easily accessible
-   Able to specify any git tag, commit or branch of the package
-   Only fetches required files unlike getting source which takes less time and bandwidth to get packages

## Requirements

-   Python >= 3.6
-   Cmake >= 3.12
-   Git >= 2.27

## Usage

See [example](./example/) for a full example.

In the project directory create a `yacpm.json` file and add the required
packages in the `packages` field as an object with the key being the
package name and value being the version (commit hash/tag/branch of repository)
or an object having the version field:

```json
{
    "packages": {
        "glfw": "3.3.4",
        "entt": "5b4ff74674063cdbc82a62ade4f5561061444013",
        "imgui": {
            "version": "docking"
        }
    }
}
```

If a branch is specified, it will be automatically converted to a commit hash
(to prevent code from suddenly breaking) unless there's a + at the front. For
example, `master` will be converted to
`3f786850e387550fdab836ed7e6dc881de23001b` but not `+master`. If the version is
an empty string yacpm will use the default branch of the repository which will
then be converted and saved as a commit. Setting the version to just `+`
will write `+` plus the default branch in yacpm.json and setting `++` will
use the default branch without saving the default branch.

Now add this to the top level CMakeLists.txt:

```cmake
if(NOT EXISTS "${CMAKE_BINARY_DIR}/yacpm.cmake")
    # Uses v3 of yacpm, replace v3 with a different number where each version is breaking change
    file(DOWNLOAD "https://github.com/Calbabreaker/yacpm/raw/v3/yacpm.cmake" "${CMAKE_BINARY_DIR}/yacpm.cmake")
endif()

include(${CMAKE_BINARY_DIR}/yacpm.cmake)
```

Now use the library in the project (all libraries names are kebab-case) as a
target (include directories are automatically set):

```cmake
# all of them in yacpm.json
target_link_libraries(${PROJECT_NAME} PRIVATE ${YACPM_PACKAGES})

# only specific ones
target_link_libraries(${PROJECT_NAME} PRIVATE glfw imgui)
```

Then run cmake:

```sh
mkdir build
cd build
cmake ..
```

Yacpm will download the package metadata (`yacpkg.json` and `CMakeLists.txt`)
and the package code using git sparse-checkout putting it all into a folder named
the package name in `yacpkgs/`.

You can also include or ignore other folders from being fetched (as an array in gitignore syntax).

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

Set the repository and cmake (a file relative to yacpm.json or url) fields to
override the repository and CMakeLists.txt in the remote. Use both of those
fields to use a library that doesn't exist in the remote like so:

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

You can also configure the package by setting cmake variables (uses CACHE FORCE
except for `BUILD_SHARED_LIBS` and `CMAKE_BUILD_TYPE`) by having a variables
object like this (this is how you configure glad):

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
and setting it globally in the top level CMakeLists.txt will link all the
libraries libraries dynamically. You might have to do a clean build before
building in order for it to build a dynamic link library.

There might also be a README.md in the packages remote directory that contains
notes on the package.

The yacpm packages that are downloaded by a yacpm package will be placed into
(or moved from `packages`) `dependency_packages` field so you can
configure the package as needed like modifying the version in case the version
provived by the package is incompatible with other packages (so manually
resolve) or you need to use that package with a specific configuration.
The `dependents` field inside the dependency package is there to show you all
the dependents as well as to delay fetching the dependency until all its dependents are
fetched.

## Additional Options

You can log all commands and their output verbose to true in `yacpm.json`:

```json
{
    "verbose": true
}
```

You can set a different package repository (default is [packages](./packages))
as either a url or local directory to download from by setting remote as an
array in `yacpm.json`. It will try to use first one and DEFAULT_REMOTE can be
use as alias to the default remote:

```json
{
    "remotes": ["https://example.com/packages", "./packages", "DEFAULT_REMOTE"]
}
```

There is also a [yacpm_extended.cmake](./yacpm_extended.cmake) file that
contains nice cmake utilities that you can use by doing:

```cmake
include(${CMAKE_BINARY_DIR}/yacpm.cmake)
yacpm_use_extended() # run after including yacpm.cmake
```

This contains a `yacpm_target_warnings(<target_list> [visibility=PRIVATE])` function
that sets strict warnings for a target. You can remove a warning by removing
items from the `YACPM_WARNINGS` list (eg. `list(REMOVE_ITEM YACPM_WARNINGS -Wshadow)`). It also enables
[ccache](https://ccache.dev/) or [sccache](https://github.com/mozilla/sccache), exports
`compile_commands.json` (for language servers), puts executables into
`build/bin`, and sets `CMAKE_BUILD_TYPE` to `Debug` if it's not set.

## Testing

Run [tests/run_tests.py](./tests/run_tests.py) to run tests in the
[tests](./tests) folder. Run
`python3 tests/run_tests.py -h` for more information. This will also be ran with
github-actions. Each test is a like integration test that tests features in
yacpm to make sure nothing breaks for users.

## Adding a new package

Create a new directory in [packages](./packages) directory with the name being
the package name. This name **must** be in kebab-case. Make a `yacpkg.json`
file with the repository of the package and directories to fetch from the
repository. The repository can be any git repository but it has to support
sparse-checkout and filter fetches which github does. Set the packages field
like in yacpm.json get any yacpm package (version should be an empty string
most of the time) that are needed for that package. Only use this if the
repository does not contain the dependency package.

```json
{
    "repository": "https://github.com/bkaradzic/bgfx",
    "include": ["/3rdparty/webgpu", "/include", "/src"],
    "packages": { "bimg": "" }
}
```

Now make a `CMakeLists.txt` in that directory. The file should be as versatile
as possible (work on as many versions) meaning add_subdirectory should be used
(unless it's simple or the CMakeListst.txt is really complex) and all files
should be globed. If the library target name is not in kebab-case, do
`add_library(library_name ALIAS LibaryName)`. The config doesn't have to work
on very old versions, just at least 1 year ago. Also use system headers for
include directories to avoid compiler warnings from the library header.

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

After everything has been tested, submit a pull request to the main branch to
have the package be in the default remote.

## Branches

The main branch contains the most recent commits where the latest potentially
breaking changes come in so it shouldn't be used. The vN (v1, v2, etc.)
branches are stable and should be used. Every time there is change that is
incompatible with previous projects using yacpm the version number will be
incremented. Also a package using yacpm must use the same version as in the top
level cmake lists in order for it to work. Any new feature that is currently
being worked on and is broken or unstable should be put into a new branch until
ready.
