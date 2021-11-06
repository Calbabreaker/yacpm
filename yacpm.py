#!/usr/bin/env python3

#
# Python script that parses a yacpm.json and downloads necessary libraries into
# yacpkgs/ directory.
#

from io import TextIOWrapper
from typing import Any, Union, Tuple
from copy import deepcopy
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request

YACPM_BRANCH = "v2"

# global variables (do not touch lines above [not including imports] or merge conflict will happen)
DIR_ARG = sys.argv[1] if len(sys.argv) > 1 else None
TOP_LEVEL_CMAKE_DIR = os.path.abspath(DIR_ARG or os.getcwd())

# utility functions

def dict_try_get(value, key: str, return_val_instead: bool = False) -> Any:
    return_val = value if return_val_instead else None
    return value.get(key) if isinstance(value, dict) else return_val

def dict_get_set(dict_input: dict, key: str, set_value):
    if key not in dict_input:
        dict_input[key] = set_value
    return dict_input[key]

def get_include_list(dictionary: dict):
    array = dictionary.get("include", [])
    include_list = ""
    for item in array:
        include_list += f' "{item}"'
    return include_list

def error(msg: str, print_wrapper: bool = True):
    text = f"==== YACPM ERROR: {msg}" if print_wrapper else msg 
    print(text, file=sys.stderr)
    exit(1)

def info(msg: str, print_wrapper: bool = True):
    msg = msg.strip()
    text = f"==== {msg}" if print_wrapper else msg
    # normal printing doesn't update realtime with cmake
    subprocess.run(f"\"{sys.executable}\" -c \"print('''{text}''')\"", shell=True)

def open_read_write(filename: str, parse_json: bool = False) -> Tuple[TextIOWrapper, Any]:
    file = open(filename, "r+")
    content = json.load(file) if parse_json else file.read()
    file.seek(0)
    return (file, content)

def write_json(data: dict, file: TextIOWrapper):
    json.dump(data, file, indent=4)
    file.truncate()
    file.close()

def download_if_missing(path: str, outfile: str) -> bool:
    if not os.path.exists(outfile):
        if path.startswith("http"):
            urllib.request.urlretrieve(path, outfile)
        else:
            file_path = os.path.join(TOP_LEVEL_CMAKE_DIR, path)
            shutil.copyfile(file_path, outfile)
        return True
    else:
        return False

def exec_shell(command: str) -> str:
    if verbose:
        info(f"> {command}", False)

    proc = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        error(proc.stderr.decode("utf-8"), False)

    stdout = proc.stdout.decode("utf-8")
    if verbose and stdout: 
        info(stdout, False)

    return stdout

# Main functions

def parse_package_version(package_version: str, package_repository: str) -> str:
    git_ref = package_version.replace("+", "")
    # get default branch if no version specifed
    if git_ref == "":
        result = exec_shell(f"git remote show {package_repository}")
        git_ref = re.findall("(?<=HEAD branch: ).+", result)[0]

    # fetch minimal info from repo with filter and depth 1 
    exec_shell(f"git fetch --depth=1 --filter=blob:none origin {git_ref}")
    exec_shell("git sparse-checkout init")
    exec_shell("git checkout FETCH_HEAD")

    # freeze if not starting with +
    if not package_version.startswith("+"):
        rev_name = exec_shell("git name-rev HEAD").strip()
        # ref-name/version is a branch
        if not rev_name.endswith("undefined"):
            # get commit hash
            package_version = exec_shell("git rev-parse HEAD").strip()
    # don't set default branch if it's ++
    elif not package_version.startswith("++"):
        package_version = "+" + git_ref

    return package_version

# returns remote that was downloaded from (if actually did download)
def download_package_metadata(remotes: set, package_name: str) -> Union[str, None]:
    for remote in remotes:
        if remote == "DEFAULT_REMOTE":
            remote = f"https://github.com/Calbabreaker/yacpm/raw/{YACPM_BRANCH}/packages"

        package_path = f"{remote}/{package_name}"
        try:
            did_download = download_if_missing(f"{package_path}/yacpkg.json", "yacpkg.json")
            did_download = download_if_missing(f"{package_path}/CMakeLists.txt", "CMakeLists-downloaded.txt")
        # try next remote if fail to download
        except (urllib.error.HTTPError, FileNotFoundError) as err:
            if isinstance(err, FileNotFoundError) or err.code == 404:
                continue
            else:
                raise

        # else return successfully
        return remote if did_download else None

    error(f"{package_name} was not found on {', '.join(remotes)}!")

def generate_cmake_variables(package_info: Union[str, dict]) -> str:
    cmake_variables = ""
    if isinstance(package_info, dict):
        # set cmake variables using CACHE FORCE to configure package
        for variable, value in package_info.get("variables", {}).items():
            if isinstance(value, bool):
                value = "ON" if value else "OFF"
                type_str = "BOOL"
            elif isinstance(value, str):
                value = f'"{value}"'
                type_str = "STRING"
            else:
                error("{variable} needs to be a string or boolean!")

            if variable == "BUILD_SHARED_LIBS":
                cmake_variables += f"set({variable} {value})\n"
            else:
                cmake_variables += f'set({variable} {value} CACHE {type_str} "" FORCE)\n'
    return cmake_variables

# calc sparse checkout list and download the neccessery package sources
def download_package_files(yacpkg: dict, package_info: Union[dict, str], progress_print: str):
    # get lists of includes from the yacpm.json package declaration and yacpkg.json package 
    # config and combines them
    sparse_checkout_list = ""
    sparse_checkout_list += get_include_list(yacpkg)
    if isinstance(package_info, dict):
        sparse_checkout_list += get_include_list(package_info)

    if yacpkg.get("^sparse_checkout_list") != sparse_checkout_list:
        info(progress_print)
        exec_shell(f"git sparse-checkout set {sparse_checkout_list}")
        yacpkg["^sparse_checkout_list"] = sparse_checkout_list

# gets all packages inside a yacpm.json and put it in a combined package
# dependencies dict to combine all the includes, variables, ect.
def get_package_dependencies(package_deps_combined: dict, remotes: set, name_to_dependent: dict, dependent_name: str):
    package_yacpm = json.load(open("yacpm.json"))

    for package_name, package_info in package_yacpm["packages"].items():
        package_in_combined = package_deps_combined.get(package_name)
        if not isinstance(package_in_combined, dict):
            package_in_combined = {}
            package_deps_combined[package_name] = package_in_combined

        dependents = package_in_combined.get("dependents", [])
        if not isinstance(dependents, set):
            package_in_combined["dependents"] = set(dependents)
            package_in_combined["dependents_left"] = set(dependents) 

        if not package_in_combined.get("version"):
            package_in_combined["version"] = dict_try_get(package_info, "version", True)

        if isinstance(package_info, dict):
            dict_get_set(package_in_combined, "include", []).extend(package_info.get("include", []))
            variables = dict_get_set(package_in_combined, "variables", {})
            for key, value in package_info.get("variables", {}).items():
                variables[key] = value

        package_in_combined["dependents"].add(dependent_name)
        package_in_combined["dependents_left"].discard(dependent_name)

        dict_get_set(name_to_dependent, package_name, []).append(dependent_name)

    # add only unique remotes from yacpm.json
    remotes |= set(package_yacpm.get("remotes", []))

# main loop that gets all package code
def get_packages(package_list: dict, remotes: set, package_deps_combined: dict, p_name_to_dependent: dict = None):
    package_names = p_name_to_dependent or list(package_list.keys())
    name_to_dependent = {}

    for i, package_name in enumerate(package_names):
        package_info = package_list[package_name]

        # if haven't parsed all dependents config yet
        dependents_left = dict_try_get(package_info, "dependents_left")
        if dependents_left and len(dependents_left) != 0:
            continue

        progress_indicator = f"[{i + 1}/{len(package_names)}]"

        output_dir = f"yacpkgs/{package_name}"
        # make the package output dir (repository dir as well for later use)
        os.makedirs(f"{output_dir}/repository", exist_ok=True)  
        os.chdir(output_dir)

        package_version = dict_try_get(package_info, "version", True)
        package_repository = dict_try_get(package_info, "repository")
        specified_cmake_file = dict_try_get(package_info, "cmake") 

        if specified_cmake_file != None:
            download_if_missing(specified_cmake_file, "CMakeLists-downloaded.txt")

        # if the user has specifed both the package repo and CMakeLists then we can
        # just use that instead downloading the package metadata
        if specified_cmake_file == None or package_repository == None:
            remote_used = download_package_metadata(remotes, package_name)
            if remote_used:
                info(f"{progress_indicator} Downloaded {package_name} package metadata from {remote_used}")

        if not os.path.exists("yacpkg.json"):
            open("yacpkg.json", "w").write("{}")

        yacpkg_file, yacpkg = open_read_write("yacpkg.json", True)

        package_repository = package_repository or yacpkg["repository"]
        os.chdir("repository")

        # initialize git repository
        if not os.path.exists(".git"):
            exec_shell("git init")
            exec_shell(f"git remote add origin {package_repository}")
            yacpkg["^current_version"] = None

        # all keys with ^ at the front was created by this script
        if yacpkg.get("^current_version") != package_version:
            info(f"{progress_indicator} Fetching {package_name}@{package_version} at {package_repository}")

            # freeze package versions that use commit hashes
            package_version = parse_package_version(package_version, package_repository)

            if isinstance(package_info, str):
                package_list[package_name] = package_version
            else:
                package_info["version"] = package_version

            if package_name in package_deps_combined:
                package_deps_combined[package_name]["version"] = package_version

            yacpkg["^current_version"] = package_version
            yacpkg["^sparse_checkout_list"] = ""

        prepend_cmake = generate_cmake_variables(package_info)

        cmake_lists_content = open("../CMakeLists-downloaded.txt").read()
        open("../CMakeLists.txt", "w").write(prepend_cmake + cmake_lists_content)

        download_print = f"{progress_indicator} Downloading files for {package_name}"
        if p_name_to_dependent and package_name in p_name_to_dependent:
            download_print += f" (required by {', '.join(p_name_to_dependent[package_name])})"
        download_package_files(yacpkg, package_info, download_print)
        write_json(yacpkg, yacpkg_file)

        # run potential yacpm config inside the yacpkgs config
        if "yacpm" in yacpkg:
            json.dump(yacpkg["yacpm"], open("yacpm.json", "w"))
            exec_shell(f"\"{sys.executable}\" {__file__} {TOP_LEVEL_CMAKE_DIR}")

        if os.path.isfile("yacpm.json"):
            get_package_dependencies(package_deps_combined, remotes, name_to_dependent, package_name)

        os.chdir(TOP_LEVEL_CMAKE_DIR)

    # use package_dep_names since package_deps_combined is a combination of all
    # iteration while package_dep_names contains package names only from this iteration
    if name_to_dependent:
        info(f"Calculating dependencies: {', '.join(name_to_dependent.keys())}")
        get_packages(package_deps_combined, remotes, package_deps_combined, name_to_dependent)

def update_package_list_deps(dependency_packages: dict, package_list: dict, package_deps_combined: dict):
    for package_name, package_info in package_deps_combined.items():
        # remove missing dependents
        dependents = package_info["dependents"]
        has_parsed_dep = isinstance(dependents, set)
        if has_parsed_dep:
            dependents.difference_update(package_info["dependents_left"])

        # if no package depends on this package remove it from list
        if len(dependents) == 0 or not has_parsed_dep:
            dependency_packages.pop(package_name)
            continue

        if package_name in package_list:
            # move package from yacpm.packages to dependency packages list
            pkg_list_pkg = package_list[package_name]
            dependency_packages[package_name] = { "version": pkg_list_pkg } if isinstance(pkg_list_pkg, str) else pkg_list_pkg
            package_list.pop(package_name)
        elif not isinstance(dependency_packages.get(package_name), dict):
            dependency_packages[package_name] = { "version": package_info["version"] }

        dependency_packages[package_name]["dependents"] = list(dependents)

if __name__ == "__main__":
    # load yacpm.json
    yacpm_file, yacpm = open_read_write("yacpm.json", True)
    verbose = yacpm.get("verbose")
    
    package_list = yacpm["packages"]
    if not isinstance(package_list, dict):
        error("Expected yacpm.json to have a packages field that is an object!")

    if not os.path.isdir("yacpkgs"):
        os.mkdir("yacpkgs")

    all_package_names = list(package_list.keys())

    # only do if is top level yacpm or if the top level yacpm.json doesn't exist
    # in order to handle multiple packages using the same package
    if TOP_LEVEL_CMAKE_DIR == os.getcwd() or not os.path.isfile(f"{TOP_LEVEL_CMAKE_DIR}/yacpm.json"):
        remotes = set(yacpm.get("remotes", ["DEFAULT_REMOTE"]))
        dependency_packages = yacpm.get("dependency_packages", {})
        package_deps_combined = deepcopy(dependency_packages)
        get_packages(package_list, remotes, package_deps_combined)

        if package_deps_combined:
            update_package_list_deps(dependency_packages, package_list, package_deps_combined)
            all_package_names.extend(dependency_packages.keys())
            if "dependency_packages" not in yacpm:
                yacpm["dependency_packages"] = dependency_packages

        write_json(yacpm, yacpm_file)

        # prune unused packages in yacpkgs
        for directory in next(os.walk("yacpkgs"))[1]:
            if directory not in package_list and directory not in dependency_packages:
                info(f"Removing unused package {directory}")
                shutil.rmtree(f"yacpkgs/{directory}")

    # write yacpkgs/packages.cmake
    packages_cmake_output = f"set(YACPM_PKGS {' '.join(all_package_names)})\n\n"
    for name in all_package_names:
        packages_cmake_output += f"if(NOT TARGET {name})\n"
        packages_cmake_output += f"    add_subdirectory(${{CMAKE_SOURCE_DIR}}/yacpkgs/{name} yacpkgs/{name})\n"
        packages_cmake_output +=  "endif()\n"
    open("yacpkgs/packages.cmake", "w").write(packages_cmake_output)
