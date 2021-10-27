#!/usr/bin/env python3

#
# Python script that parses a yacpm.json and downloads necessary libraries into
# yacpkgs/ directory.
#

from io import TextIOWrapper
from typing import Any, Union
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request

YACPM_BRANCH = "main"

# global variables (do not touch lines above [not including imports] or merge conflict will happen)
TOP_LEVEL_CMAKE_DIR = os.path.abspath(sys.argv[1] or os.getcwd())

# utility functions

def ensure_array(value):
    return value if isinstance(value, list) else [value];

def dict_try_get(value: Union[Any, dict], key: str):
    return value.get(key) if isinstance(value, dict) else None

def get_include_list(dictionary: dict):
    array = ensure_array(dictionary.get("include", []))
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

def open_read_write(filename: str, parse_json: bool = False) -> tuple[TextIOWrapper, Any]:
    file = open(filename, "r+")
    content = json.load(file) if parse_json else file.read()
    file.seek(0)
    return (file, content)

def write_json(data: dict, file: TextIOWrapper):
    json.dump(data, file, indent=4)
    file.truncate()

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
def download_package_metadata(remotes: set[str], package_name: str) -> Union[str, None]:
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

    error(f"{package_name} was not found on the remote(s)!")

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

# calc sparse checkout list and actually download the package sources
def download_package_files(yacpkg: dict, package_info: Union[dict, str], progress_print: str):
    # get lists of includes from the yacpm.json package declaration and yacpkg.json package 
    # config and combines them
    sparse_checkout_list = ""
    sparse_checkout_list += get_include_list(yacpkg)
    if isinstance(package_info, dict):
        sparse_checkout_list += get_include_list(package_info)

    if yacpkg.get("^sparse_checkout_list") != sparse_checkout_list:
        # git sparse checkout list will download only the necessery directories of the repository
        info(progress_print);
        exec_shell(f"git sparse-checkout set {sparse_checkout_list}")
        yacpkg["^sparse_checkout_list"] = sparse_checkout_list

# gets all packages inside a yacpm.json and put it in a combined package
# dependencies dict to combine all the includes, variables, ect.
def get_package_dependencies(package_deps_combined: dict, remotes: set[str]):
    yacpm = json.load(open("yacpm.json"))
    for package_name, package_info in yacpm["packages"].items():
        package_in_combined = package_deps_combined.get(package_name)
        if package_in_combined == None:
            package_in_combined = {"variables": {}, "include": []}
            package_deps_combined[package_name] = package_in_combined

        if isinstance(package_info, str):
            package_in_combined["version"] = package_info
        else:
            package_in_combined["version"] = package_info["version"]
            package_in_combined["include"] += package_info.get("include", [])

            for key, value in package_info.get("variables", {}).items():
                package_in_combined[key] = value

    # add only unique remotes from yacpm.json
    remotes |= set(ensure_array(yacpm.get("remotes", [])))

def get_packages(package_list: dict, remotes: set[str], package_deps_combined: dict):
    package_names = package_list.keys()

    for i, package_name in enumerate(package_names):
        package_info = package_list[package_name]
        progress_indicator = f"[{i + 1}/{len(package_names)}]"

        output_dir = f"yacpkgs/{package_name}"
        # make the package output dir (repository dir as well for later use)
        os.makedirs(f"{output_dir}/repository", exist_ok=True)  
        os.chdir(output_dir)

        # checks if package info is an object containing the version field or it's the version as a string 
        package_version = package_info["version"] if isinstance(package_info, dict) else package_info
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
            yacpkg["^current_version"] = package_version
            yacpkg["^sparse_checkout_list"] = ""

        prepend_cmake = generate_cmake_variables(package_info)

        cmake_lists_content = open("../CMakeLists-downloaded.txt").read()
        open("../CMakeLists.txt", "w").write(prepend_cmake + cmake_lists_content)

        download_print = f"{progress_indicator} Downloading files for {package_name}";
        download_package_files(yacpkg, package_info, download_print)

        if "yacpm" in yacpkg:
            json.dump(yacpkg["yacpm"], open("yacpm.json", "w"))
            exec_shell(f"\"{sys.executable}\" {__file__} {os.getcwd()}")

        if os.path.isfile("yacpm.json"):
            get_package_dependencies(package_deps_combined, remotes)

        write_json(yacpkg, yacpkg_file)
        os.chdir(TOP_LEVEL_CMAKE_DIR)

    if not package_deps_combined:
        return

    for package_name, package_info in package_deps_combined.items():
        if package_name not in package_list:
            package_list[package_name] = {"version": package_info.version, "dependency": True}


    get_packages(package_deps_combined, remotes, package_deps_combined)

if __name__ == "__main__":
    # load yacpm.json
    yacpm_file, yacpm = open_read_write("yacpm.json", True)
    verbose = yacpm.get("verbose")
    
    if not "packages" in yacpm or not isinstance(yacpm["packages"], dict):
        error("Expected yacpm.json to have a packages field that is an object!")

    if not os.path.isdir("yacpkgs"):
        os.mkdir("yacpkgs")

    # write yacpkgs/packages.cmake
    package_names = yacpm["packages"].keys()
    packages_cmake_output = f"set(YACPM_PKGS {' '.join(package_names)})\n"
    for name in package_names:
        packages_cmake_output += f"\nadd_subdirectory(${{CMAKE_SOURCE_DIR}}/yacpkgs/{name} yacpkgs/{name})"
    open("yacpkgs/packages.cmake", "w").write(packages_cmake_output)

    # make the top level yacpm.json get the packages instead if that exists in
    # order to handle multiple packages using the same package
    if TOP_LEVEL_CMAKE_DIR != os.getcwd() and os.path.isfile(f"{TOP_LEVEL_CMAKE_DIR}/yacpm.json"):
        exit()

    if not os.path.isfile("yacpkgs/cache.json"):
        open("yacpkgs/cache.json", "w").write("{}")

    remotes = set(ensure_array(yacpm.get("remote", "DEFAULT_REMOTE")))
    cache_file, cache = open_read_write("yacpkgs/cache.json", True)
    get_packages(yacpm["packages"], remotes)
    write_json(cache, cache_file)
    write_json(yacpm, yacpm_file)

    # prune unused packages in yacpkgs
    for directory in next(os.walk("yacpkgs"))[1]:
        if directory not in yacpm["packages"]:
            info(f"Removing unused package {directory}")
            shutil.rmtree(f"yacpkgs/{directory}")
