#!/usr/bin/env python3

#
# Python script that parses a yacpm.json and downloads necessary libraries into
# yacpkgs/ directory.
#

from io import TextIOWrapper
from typing import Any, Tuple, Union, List
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request

YACPM_BRANCH = "main"

# global variable (do not touch lines [not including imports] above or merge conflict will happen)
YACPM_DEFAULT_REMOTE_URL = f"https://github.com/Calbabreaker/yacpm/raw/{YACPM_BRANCH}/packages"
YACPKGS_OUTPUT_DIR = os.path.abspath(sys.argv[1] or os.getcwd())

# utility functions

def ensure_array(value):
    return value if isinstance(value, list) else [value];

def dict_try_get(value: Union[Any, dict], key: str):
    return value.get(key) if isinstance(value, dict) else None

def get_include_list(dictionary: dict):
    array = ensure_array(dictionary.get("include", []))
    include_list = ""
    for item in array:
        include_list += f" '{item}'"
    return include_list

def error(msg: str, print_wrapper: bool = True):
    text = f"==== YACPM ERROR: {msg}" if print_wrapper else msg 
    print(text, file=sys.stderr)
    exit(1)

def info(msg: str, print_wrapper: bool = True):
    text = f"==== {msg}" if print_wrapper else msg
    # normal printing doesn't update realtime with cmake
    os.system(f"echo \"{text}\"")

def open_read_write(filename: str, parse_json: bool = False) -> Tuple[TextIOWrapper, Any]:
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
            file_path = os.path.join(YACPKGS_OUTPUT_DIR, path)
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
    exec_shell(f"git fetch --depth 1 --filter=blob:none origin {git_ref}")
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
def download_package_metadata(remotes: List[str], package_name: str) -> Union[str, None]:
    for remote in remotes:
        package_path = f"{remote}/{package_name}"
        try:
            did_download = download_if_missing(f"{package_path}/yacpkg.json", "yacpkg.json")
            did_download |= download_if_missing(f"{package_path}/CMakeLists.txt", "CMakeLists-downloaded.txt")
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
        return True
    else:
        return False

if __name__ == "__main__":
    # load yacpm.json
    yacpm_file, yacpm = open_read_write("yacpm.json", True)
    verbose = yacpm.get("verbose", False)

    if not "packages" in yacpm or not isinstance(yacpm["packages"], dict):
        error("Expected yacpm.json to have a packages field that is an object!")

    if YACPKGS_OUTPUT_DIR != os.getcwd() and os.path.isfile(f"{YACPKGS_OUTPUT_DIR}/yacpm.json"):
        top_level_yacpm_file, top_level_yacpm = open_read_write(f"{YACPKGS_OUTPUT_DIR}/yacpm.json", True)
        for package_name, package_info in top_level_yacpm_file


    # replaces DEFAUL_REMOTE default remote url for ease of use
    remotes = ensure_array(yacpm.get("remote", "DEFAULT_REMOTE"))
    remotes = [YACPM_DEFAULT_REMOTE_URL if r == "DEFAULT_REMOTE" else r for r in remotes]

    package_names = yacpm["packages"].keys()
    for i, package_name in enumerate(package_names):
        package_info = yacpm["packages"][package_name]
        progress_indicator = f"[{i + 1}/{len(package_names)}]"

        output_dir = os.path.join(YACPKGS_OUTPUT_DIR, f"yacpkgs/{package_name}")

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

            # Freeze package versions that use commit hashes
            package_version = parse_package_version(package_version, package_repository)

            if isinstance(package_info, str):
                yacpm["packages"][package_name] = package_version
            else:
                package_info["version"] = package_version
            yacpkg["^current_version"] = package_version
            yacpkg["^sparse_checkout_list"] = ""

        prepend_cmake = generate_cmake_variables(package_info)

        cmake_lists_content = open("../CMakeLists-downloaded.txt").read()
        open("../CMakeLists.txt", "w").write(prepend_cmake + cmake_lists_content)

        download_print = f"{progress_indicator} Downloading files for {package_name}";
        fetched_files = download_package_files(yacpkg, package_info, download_print)

        if "yacpm" in yacpkg:
            file = open("yacpm.json", "w")
            write_json(yacpkg["yacpm"], yacpkg_file)
            info(f"-- Running {__file__} for {package_name}", False)
            os.system(f"python3 {__file__}")

        write_json(yacpkg, yacpkg_file)
        os.chdir(YACPKGS_OUTPUT_DIR)

    # prune unused packages in yacpkgs
    for directory in next(os.walk("yacpkgs"))[1]:
        if directory not in yacpm["packages"]:
            info(f"Removing unused package {directory}")
            shutil.rmtree(f"yacpkgs/{directory}")

    # generate packages.cmake
    include_file_output = f"set(YACPM_PKGS {' '.join(package_names)})\n"
    for name in package_names:
        include_file_output += f"\nadd_subdirectory(${{CMAKE_SOURCE_DIR}}/yacpkgs/{name})"
    open("yacpkgs/packages.cmake", "w").write(include_file_output)

    write_json(yacpm, yacpm_file)
