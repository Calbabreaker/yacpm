#!/usr/bin/env python3

#
# Python script that parses a yacpm.json and downloads necessery libraries into
# yacpkgs/ directory.
#

from typing import Any, Tuple, List
from io import TextIOWrapper
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request

YACPM_BRANCH = "v1"

# utility functions
def get_includes(dictionary):
    value = dictionary.get("include", [])
    return value if isinstance(value, list) else [value]

def error(msg: str, print_wrapper: bool = True):
    text = f"==== YACPM ERROR: {msg}" if print_wrapper else msg 
    print(text, file=sys.stderr)
    exit(1)

def info(msg: str, print_wrapper: bool = True):
    # normal printing doesn't update realtime with cmake
    text = f"==== {msg}" if print_wrapper else msg
    os.system(f"python -c 'print (\"{text}\")'")

def open_read_write(filename: str, parse_json: bool = False) -> Tuple[TextIOWrapper, Any]:
    file = open(filename, "r+")
    content = json.load(file) if parse_json else file.read()
    file.seek(0)
    return (file, content)

def write_json(data: dict, file: TextIOWrapper):
    json.dump(data, file, indent=4)
    file.truncate()

if __name__ == "__main__":
    # load yacpm.json
    project_dir = os.getcwd()
    yacpm_file, yacpm = open_read_write("yacpm.json", True)
    remote_url: str = yacpm.get("remote", f"https://raw.githubusercontent.com/Calbabreaker/yacpm/{YACPM_BRANCH}/packages")

    def download_not_exist(url: str, outfile: str):
        if not os.path.exists(outfile):
            info(f"Downloading {url}...")
            if remote_url.startswith("http"):
                urllib.request.urlretrieve(url, outfile)
            else:
                shutil.copyfile(f"{project_dir}/{url}", outfile)

    def exec_shell(command: str) -> str:
        proc = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if proc.returncode != 0:
            error(proc.stderr.decode("utf-8"), False)

        stdout = proc.stdout.decode("utf-8")
        
        if yacpm.get("verbose"):
            info(f"> {command}", False)
            info(stdout, False)

        return stdout

    if not "packages" in yacpm or not isinstance(yacpm["packages"], dict):
        error("Expected yacpm.json to have a packages field that is an object!")

    for package_name, package_info in yacpm["packages"].items():
        package_url = f"{remote_url}/{package_name}"
        output_dir = f"yacpkgs/{package_name}"

        # make the package output dir (repository dir as well for later use)
        os.makedirs(f"{output_dir}/repository", exist_ok=True)  
        os.chdir(output_dir)

        # check if package info a object containing the version field or it's the version as a string 
        info_is_str = isinstance(package_info, str) 
        package_version = package_info if info_is_str else package_info["version"] 

        package_repository = package_info.get("repository") if not info_is_str else None
        specified_cmake_file = package_info.get("cmake") if not info_is_str else None

        # if the user has specifed both the package repo and CMakeLists then we can
        # just use that instead of fetching the remote
        if package_repository != None and specified_cmake_file != None:
            shutil.copyfile(f"{project_dir}/{specified_cmake_file}", "CMakeLists.txt")
        else:
            try:
                download_not_exist(f"{package_url}/yacpkg.json", "yacpkg.json")
            except urllib.error.HTTPError as err:
                if err.code == 404:
                    error(f"{package_name} was not found on {remote_url}")
                else:
                    raise
            
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
            version = package_version.replace("+", "")
            info(f"Fetching repository version {version} for {package_name} at {package_repository}")

            # fetch minimal info from repo with filter and depth 1 
            exec_shell(f"git fetch --depth 1 --filter=blob:none origin {version}")
            exec_shell("git sparse-checkout init --cone")
            exec_shell("git checkout FETCH_HEAD")

            if not package_version.startswith("+"):
                rev_name = exec_shell("git name-rev HEAD").strip()
                # ref-name/version is a branch
                if not rev_name.endswith("undefined"):
                    # get commit hash
                    package_version = exec_shell("git rev-parse HEAD").strip()
                    if info_is_str:
                        yacpm["packages"][package_name] = package_version
                    else:
                        package_info["version"] = package_version

            if specified_cmake_file == None and os.path.exists("../CMakeLists.txt"):
                os.remove("../CMakeLists.txt")

            yacpkg["^current_version"] = package_version

        download_not_exist(f"{package_url}/CMakeLists.txt", "../CMakeLists.txt")

        # set cmake variables using CACHE FORCE configure package
        extra_cmake = ""
        if not info_is_str:
            for variable, value in package_info.get("variables", {}).items():
                if isinstance(value, bool):
                    value = "ON"
                    type_str = "BOOL"
                elif isinstance(value, str):
                    value = f'"{value}"'
                    type_str = "STRING"
                else:
                    error("{variable} needs to be a string or boolean!")

                extra_cmake += f'set({variable} {value} CACHE {type_str} "" FORCE)\n'

        open("../extra.cmake", "w").write(extra_cmake)

        # prepend include(extra.cmake) to CMakeLists.txt
        cmake_include = "include(extra.cmake)\n"
        file, content = open_read_write("../CMakeLists.txt")
        if not content.startswith(cmake_include):
            file.write(cmake_include + content)

        # get lists of includes from the yacpm.json package declaration or yacpkg.json package 
        # config and combine them
        sparse_checkout_array: List[str] = []
        sparse_checkout_array += get_includes(yacpkg)
        if not info_is_str:
            sparse_checkout_array += get_includes(package_info)
        sparse_checkout_list = " ".join(sparse_checkout_array)

        # git sparse checkout list will download only the necessery directories of the repository
        if sparse_checkout_list != "" and yacpkg.get("^sparse_checkout_list") != sparse_checkout_list:
            info(f"Fetching directories {sparse_checkout_array} for package {package_name}")

            exec_shell(f"git sparse-checkout set {sparse_checkout_list}")
            yacpkg["^sparse_checkout_list"] = sparse_checkout_list

        write_json(yacpkg, yacpkg_file)
        os.chdir(project_dir)

    # prune unused packages in yacpkgs
    for directory in next(os.walk("yacpkgs"))[1]:
        if directory not in yacpm["packages"]:
            info(f"Removing unused package {directory}")
            shutil.rmtree(f"yacpkgs/{directory}")

    package_names = yacpm["packages"].keys()
    include_file_output = f"set(YACPM_LIBS {' '.join(package_names)})\n"
    for name in package_names:
        include_file_output += f"\nadd_subdirectory(${{CMAKE_CURRENT_SOURCE_DIR}}/yacpkgs/{name})"
    open("yacpkgs/packages.cmake", "w").write(include_file_output)

    write_json(yacpm, yacpm_file)
