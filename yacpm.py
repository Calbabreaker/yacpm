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
PROJECT_DIR = os.getcwd()

# utility functions

def dict_try_get(value, key: str, return_val_instead_none: bool = False) -> Any:
    return_val = value if return_val_instead_none else None
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

def write_packages_cmake(package_names):
    if not os.path.exists("yacpkgs"):
        os.mkdir("yacpkgs")
    cmake_output = f"set(YACPM_PKGS {' '.join(package_names)})\n"
    cmake_output += "foreach(PKG ${YACPM_PKGS})\n"
    cmake_output += "    if(NOT TARGET ${PKG})\n"
    cmake_output += "        add_subdirectory(${CMAKE_SOURCE_DIR}/yacpkgs/${PKG} yacpkgs/${PKG})\n"
    cmake_output += "    endif()\n"
    cmake_output += "endforeach()"
    open("yacpkgs/packages.cmake", "w").write(cmake_output)

def download_if_missing(path: str, outfile: str) -> bool:
    if not os.path.exists(outfile):
        if path.startswith("http"):
            urllib.request.urlretrieve(path, outfile)
        else:
            file_path = os.path.join(PROJECT_DIR, path)
            shutil.copyfile(file_path, outfile)
        return True
    else:
        return False

def exec_shell(command: str) -> str:
    proc = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        error(proc.stderr.decode("utf-8"), False)

    stdout = proc.stdout.decode("utf-8")
    
    if verbose:
        info(f"> {command}", False)
        if stdout: 
            info(stdout, False)

    return stdout

# Main functions

def parse_package_version(package_version: str) -> str:
    git_ref = package_version.replace("+", "")
    # get default branch if no version specifed
    if git_ref == "":
        result = exec_shell(f"git remote show origin")
        git_ref = re.findall("(?<=HEAD branch: ).+", result)[0]

    # fetch/init repo with least amount of downloading
    exec_shell(f"git fetch --depth=1 --filter=blob:none origin {git_ref}")
    exec_shell("git sparse-checkout init")
    exec_shell("git checkout FETCH_HEAD")

    # don't freeze if version starting with +
    if not package_version.startswith("+"):
        rev_name = exec_shell("git name-rev HEAD").strip()
        # version is a branch then convert to commit
        if not rev_name.endswith("undefined"):
            package_version = exec_shell("git rev-parse HEAD").strip()
    # don't set default branch if it's ++
    elif not package_version.startswith("++"):
        package_version = "+" + git_ref

    return package_version

# returns remote that was downloaded from (if actually did download)
def download_package_metadata(remotes: list, package_name: str) -> Union[str, None]:
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

    error(f"{package_name} was not found on any of these remotes: {', '.join(remotes)}!")

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

# calc sparse checkout list and download the neccessery package files
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
def get_package_dependencies(package_deps_combined: dict, remotes: list, next_iter_package_names: set, dependent_name: str):
    package_yacpm = json.load(open("yacpm.json"))

    package_list: dict = package_yacpm["packages"]
    package_list.update(package_yacpm.get("dependency_packages", {}))
    for package_name, package_info in package_list.items():
        package_in_combined = package_deps_combined.get(package_name)
        if not isinstance(package_in_combined, dict):
            package_in_combined = {}
            package_deps_combined[package_name] = package_in_combined

        # convert to sets to ensure no duplicate dependent names
        dependents = package_in_combined.get("dependents", [])
        if not isinstance(dependents, set):
            package_in_combined["dependents"] = set(dependents)
            package_in_combined["dependents_left"] = set(dependents) 

        if not package_in_combined.get("version"):
            package_in_combined["version"] = dict_try_get(package_info, "version", True)

        if isinstance(package_info, dict):
            includes = dict_get_set(package_in_combined, "include", [])
            includes[0:0] = package_info.get("include", []) # prepends

            variables = dict_get_set(package_in_combined, "variables", {})
            for key, value in package_info.get("variables", {}).items():
                variables[key] = value

        package_in_combined["dependents"].add(dependent_name)
        package_in_combined["dependents_left"].discard(dependent_name)

    # prepend to remotes to give those remotes piority
    remotes[0:0] = package_yacpm.get("remotes", [])

    package_names = package_list.keys()
    next_iter_package_names.update(package_names)
    write_packages_cmake(package_names)

# main loop that gets all package code
def get_packages(package_list: dict, remotes: list, package_deps_combined: dict, package_names = None):
    package_names = package_names or package_list.keys() # iteratable type
    next_iter_package_names = set()

    for i, package_name in enumerate(package_names):
        package_info = package_list[package_name]

        # if haven't parsed fetched all dependents yet (optimization)
        if dict_try_get(package_info, "dependents_left"):
            continue

        progress_indicator = f"[{i + 1}/{len(package_names)}]"

        output_dir = f"yacpkgs/{package_name}"
        # make the package output dir (repository dir as well for later use)
        os.makedirs(f"{output_dir}/repository", exist_ok=True)  
        os.chdir(output_dir)

        package_version = dict_try_get(package_info, "version", True)
        package_repository = dict_try_get(package_info, "repository")
        specified_cmake_file = dict_try_get(package_info, "cmake") 

        if specified_cmake_file:
            download_if_missing(specified_cmake_file, "CMakeLists-downloaded.txt")

        # if the user has specifed both the package repo and CMakeLists then we can
        # just use that instead downloading the package metadata
        if not specified_cmake_file or not package_repository:
            remote_used = download_package_metadata(remotes, package_name)
            if remote_used:
                info(f"{progress_indicator} Downloaded {package_name} package metadata from {remote_used}")

        # if didn't download yacpkg.json file then create it
        if not os.path.exists("yacpkg.json"):
            open("yacpkg.json", "w").write("{}")
        yacpkg_file, yacpkg = open_read_write("yacpkg.json", True)

        os.chdir("repository")

        # if user didn't specify repository
        package_repository = package_repository or yacpkg["repository"]

        # initialize git repository
        if not os.path.exists(".git"):
            exec_shell("git init")
            exec_shell(f"git remote add origin {package_repository}")
            yacpkg["^current_version"] = None

        # all keys with ^ at the front was created by this script
        if yacpkg.get("^current_version") != package_version:
            # freeze package versions that use commit hashes
            info(f"{progress_indicator} Fetching {package_name}@{package_version} at {package_repository}")
            package_version = parse_package_version(package_version)

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
        download_package_files(yacpkg, package_info, download_print)
        write_json(yacpkg, yacpkg_file)

        # run potential yacpm config inside the yacpkg.json
        if "packages" in yacpkg:
            json.dump({ "packages": yacpkg["packages"] }, open("yacpm.json", "w"))

        if os.path.isfile("yacpm.json"):
            get_package_dependencies(package_deps_combined, remotes, next_iter_package_names, package_name)

        os.chdir(PROJECT_DIR)

    if next_iter_package_names:
        info(f"Calculating dependencies: {', '.join(next_iter_package_names)}")
        get_packages(package_deps_combined, remotes, package_deps_combined, next_iter_package_names)

def update_package_list_deps(dependency_packages: dict, package_list: dict, package_deps_combined: dict):
    for package_name, package_info in package_deps_combined.items():
        # remove missing dependents
        dependents = package_info["dependents"]
        has_parsed_dep = isinstance(dependents, set)
        if has_parsed_dep:
            dependents.difference_update(package_info["dependents_left"])

        # if no package depends on this package move it back to normal package list
        if len(dependents) == 0 or not has_parsed_dep:
            package_list[package_name] = dependency_packages[package_name]
            package_list[package_name].pop("dependents")
            dependency_packages.pop(package_name)
            continue

        if package_name in package_list:
            # move package from normal packages list to dependency packages list
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
    
    package_list: dict = yacpm["packages"]
    remotes = yacpm.get("remotes", ["DEFAULT_REMOTE"])
    dependency_packages = yacpm.get("dependency_packages", {})
    package_deps_combined = deepcopy(dependency_packages)
    get_packages(package_list, remotes, package_deps_combined)

    if package_deps_combined:
        update_package_list_deps(dependency_packages, package_list, package_deps_combined)
        if "dependency_packages" not in yacpm:
            yacpm["dependency_packages"] = dependency_packages

    write_json(yacpm, yacpm_file)

    # prune unused packages in yacpkgs
    for directory in next(os.walk("yacpkgs"))[1]:
        if directory not in package_list and directory not in dependency_packages:
            info(f"Removing unused package {directory}")
            shutil.rmtree(f"yacpkgs/{directory}")

    all_package_names = list(package_list.keys())
    all_package_names.extend(package_deps_combined.keys())
    write_packages_cmake(all_package_names)

