#!/usr/bin/env python3

#
# Python script that parses a yacpm.json and downloads necessary libraries into
# yacpkgs/ directory.
#

from io import TextIOWrapper
from typing import Any, Tuple
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request

YACPM_BRANCH = "main"
YACPM_PACKAGES_URL_TEMPLATE = "https://github.com/Calbabreaker/yacpm/raw/{}/packages"

# utility functions
def get_include_list(dictionary: dict):
    value = dictionary.get("include", [])
    array = value if isinstance(value, list) else [value]
    include_list = ""
    for item in array:
        include_list += f" '{item}'"
    return include_list

def error(msg: str, print_wrapper: bool = True):
    text = f"==== YACPM ERROR: {msg}" if print_wrapper else msg 
    print(text, file=sys.stderr)
    exit(1)

def info(msg: str, print_wrapper: bool = True):
    # normal printing doesn't update realtime with cmake
    text = f"==== {msg}" if print_wrapper else msg
    os.system(f"python3 -c 'print(\"\"\"{text}\"\"\")'")

def open_read_write(filename: str, parse_json: bool = False) -> Tuple[TextIOWrapper, Any]:
    file = open(filename, "r+")
    content = json.load(file) if parse_json else file.read()
    file.seek(0)
    return (file, content)

def write_json(data: dict, file: TextIOWrapper):
    json.dump(data, file, indent=4)
    file.truncate()

def download_if_missing(project_dir: str, url: str, outfile: str):
    if not os.path.exists(outfile):
        if yacpm.get("verbose"):
            info(f"Downloading {url}...")

        if url.startswith("http"):
            urllib.request.urlretrieve(url, outfile)
        else:
            if not os.path.isabs(url):
                url = f"{project_dir}/{url}"
            shutil.copyfile(url, outfile)

def exec_shell(command: str, verbose: bool) -> str:
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

def convert_package_version_to_commit_hash(package_version, package_repository) -> str:
    # Yes is long function name. Feel free to improve
    version = package_version.replace("+", "")
    # get default branch if no version specifed
    if version == "":
        result = exec_shell(f"git remote show {package_repository}")
        version = re.findall("(?<=HEAD branch: ).+", result)[0]

    # fetch minimal info from repo with filter and depth 1 
    exec_shell(f"git fetch --depth 1 --filter=blob:none origin {version}")
    exec_shell("git sparse-checkout init")
    exec_shell("git checkout FETCH_HEAD")

    if not package_version.startswith("+"):
        rev_name = exec_shell("git name-rev HEAD").strip()
        # ref-name/version is a branch
        if not rev_name.endswith("undefined"):
            # get commit hash
            package_version = exec_shell("git rev-parse HEAD").strip()
    return package_version

def download_package_metadata(package_repository: str, specified_cmake_file: str):
    # if the user has specifed both the package repo and CMakeLists then we can
    # just use that instead of fetching the remote
    if package_repository != None and specified_cmake_file != None:
        download_if_missing(specified_cmake_file, "CMakeLists-downloaded.txt")
    else:
        try:
            download_if_missing(f"{package_url}/yacpkg.json", "yacpkg.json")
            download_if_missing(f"{package_url}/CMakeLists.txt", "CMakeLists-downloaded.txt")
        except urllib.error.HTTPError as err:
            if err.code == 404:
                error(f"{package_name} was not found on {remote_url}")
            else:
                raise

def generate_cmake_variables(package_info) -> str:
    cmake_variables = ""
    # If the package info is not just a version
    if not isinstance(package_info, str):
        # set cmake variables using CACHE FORCE configure package
        for variable, value in package_info.get("variables", {}).items():
            if isinstance(value, bool):
                value = "ON" if value else "OFF"
                type_str = "BOOL"
            elif isinstance(value, str):
                value = f'"{value}"'
                type_str = "STRING"
            else:
                error("{variable} needs to be a string or boolean!")

            cmake_variables += f'set({variable} {value} CACHE {type_str} "" FORCE)\n'
    return cmake_variables

def download_package(yacpkg, package_info) -> bool:
    # Calc sparse checkout list and actually download the package sources
    # Returns bool stating if it fetched files

    # get lists of includes from the yacpm.json package declaration and yacpkg.json package 
    # config and combines them
    sparse_checkout_list = ""
    sparse_checkout_list += get_include_list(yacpkg)
    if not package_info_is_str:
        sparse_checkout_list += get_include_list(package_info)

    fetched_files = False

    # git sparse checkout list will download only the necessery directories of the repository
    if sparse_checkout_list != "" and yacpkg.get("^sparse_checkout_list") != sparse_checkout_list:
        exec_shell(f"git sparse-checkout set {sparse_checkout_list}")
        yacpkg["^sparse_checkout_list"] = sparse_checkout_list
        fetched_files = True

    return fetched_files

if __name__ == "__main__":
    # load yacpm.json
    project_dir = os.getcwd()
    yacpm_file, yacpm = open_read_write("yacpm.json", True)
    remote_url: str = yacpm.get("remote", YACPM_PACKAGES_URL_TEMPLATE.format(YACPM_BRANCH))

    if not "packages" in yacpm or not isinstance(yacpm["packages"], dict):
        error("Expected yacpm.json to have a packages field that is an object!")

    package_names = yacpm["packages"].keys()
    for i, package_name in enumerate(package_names):
        package_info = yacpm["packages"][package_name]
        progress_indicator = f"[{i + 1}/{len(package_names)}]"

        package_url = f"{remote_url}/{package_name}"
        output_dir = f"yacpkgs/{package_name}"

        # make the package output dir (repository dir as well for later use)
        os.makedirs(f"{output_dir}/repository", exist_ok=True)  
        os.chdir(output_dir)

        # check if package info a object containing the version field or it's the version as a string 
        package_info_is_str = isinstance(package_info, str) 
        package_version = package_info if package_info_is_str else package_info["version"] 

        package_repository = package_info.get("repository") if not package_info_is_str else None
        specified_cmake_file = package_info.get("cmake") if not package_info_is_str else None

        download_package_metadata(package_repository, specified_cmake_file)
            
        if not os.path.exists("yacpkg.json"):
            open("yacpkg.json", "w").write("{}")

        yacpkg_file, yacpkg = open_read_write("yacpkg.json", True)

        package_repository = package_repository or yacpkg["repository"]
        os.chdir("repository")

        # initialize git repository
        if not os.path.exists(".git"):
            exec_shell("git init", yacpm.get("verbose"))
            exec_shell(f"git remote add origin {package_repository}", yacpm.get("verbose"))
            yacpkg["^current_version"] = None

        # Freeze the package version with a commit hash
        # all keys with ^ at the front was created by this script
        if yacpkg.get("^current_version") != package_version:
            package_version = \
                convert_package_version_to_commit_hash(package_version, package_repository)

            info(f"{progress_indicator} Fetching {package_name}@{package_version} at {package_repository}")

            if isinstance(package_info, str):
                yacpm["packages"][package_name] = package_version
            else:
                package_info["version"] = package_version
            yacpkg["^current_version"] = package_version

        prepend_cmake = generate_cmake_variables(package_info)
        cmake_lists_content = open("../CMakeLists-downloaded.txt").read()
        open("../CMakeLists.txt", "w").write(prepend_cmake + cmake_lists_content)

        fetched_files = download_package(yacpkg, package_info)
        if fetched_files:
            info(f"{progress_indicator} Fetching files for {package_name}")

        write_json(yacpkg, yacpkg_file)
        os.chdir(project_dir)

    # prune unused packages in yacpkgs
    for directory in next(os.walk("yacpkgs"))[1]:
        if directory not in yacpm["packages"]:
            info(f"Removing unused package {directory}")
            shutil.rmtree(f"yacpkgs/{directory}")

    include_file_output = f"set(YACPM_PKGS {' '.join(package_names)})\n"
    for name in package_names:
        include_file_output += f"\nadd_subdirectory(${{CMAKE_CURRENT_SOURCE_DIR}}/yacpkgs/{name})"
    open("yacpkgs/packages.cmake", "w").write(include_file_output)

    write_json(yacpm, yacpm_file)
