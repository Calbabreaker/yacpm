#!/usr/bin/env python3

#
# Python script that parses a yacpm.json and downloads necessery libraries into
# yacpkgs/ directory.
#

import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request

YACPM_BRANCH = "main"

project_dir = os.getcwd()
yacpm = json.load(open("yacpm.json"))
remote_url = yacpm.get("remote", f"https://raw.githubusercontent.com/Calbabreaker/yacpm/{YACPM_BRANCH}/packages")

def error(msg: str, print_wrapper: bool = True):
    text = f"==== YACPM ERROR: {msg}" if print_wrapper else msg 
    print(text, file=sys.stderr)
    exit(1)

def exec_shell(command: str):
    if yacpm.get("verbose"):
        if os.system(command) != 0:
            exit(1)
    else:
        proc = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # errors are not silented
        if proc.returncode != 0:
            error(proc.stderr.decode("utf-8"), False)

def info(msg: str):
    # normal printing doesn't update realtime with cmake
    os.system(f"python -c 'print (\"==== {msg}\")'")

def download_not_exist(url: str, outfile: str):
    if not os.path.isfile(outfile):
        info(f"Downloading {url}...")
        urllib.request.urlretrieve(url, outfile)

def ensure_array(value):
    return value if isinstance(value, list) else [value]

if not "packages" in yacpm or not isinstance(yacpm["packages"], dict):
    error("Expected yacpm.json to have a packages field that is an object!")

for package_name, package_info in yacpm["packages"].items():
    # make directories
    output_dir = f"yacpkgs/{package_name}"
    os.makedirs(f"{output_dir}/repository", exist_ok=True) # make the repository dir as well for later use
    os.chdir(output_dir)

    # check if package info a object containing the version field or it's the version as a string 
    info_is_str = isinstance(package_info, str) 
    package_version = package_info if info_is_str else package_info["version"] 

    package_repository = package_info.get("repository") if not info_is_str else None
    specified_cmake_filepath = package_info.get("cmake") if not info_is_str else None
    
    # if the user has specifed both the package repo and CMakeLists then we can
    # just use that instead of fetching the remote
    if package_repository != None and specified_cmake_filepath != None:
        shutil.copyfile(f"{project_dir}/{specified_cmake_filepath}", "CMakeLists.txt")
    else:
        try:
            package_url = f"{remote_url}/{package_name}"
            download_not_exist(f"{package_url}/CMakeLists.txt", "CMakeLists.txt")
            download_not_exist(f"{package_url}/yacpkg.json", "yacpkg.json")
        except urllib.error.HTTPError as err:
            if err.code == 404:
                error(f"{package_name} was not found on {remote_url}")
            else:
                raise
        
    if os.path.exists("yacpkg.json"):
        yacpkg_file = open("yacpkg.json", "r+")
        yacpkg = json.load(yacpkg_file)
    else:
        yacpkg_file = open("yacpkg.json", "w")
        yacpkg = {}

    package_repository = package_repository or yacpkg["repository"]

    os.chdir("repository")

    # initialize git repository
    if not os.path.isdir(".git"):
        exec_shell("git init")
        exec_shell(f"git remote add origin {package_repository}")
        yacpkg["^current_version"] = None

    # all keys with ^ at the front was created by this script
    if yacpkg.get("^current_version") != package_version:
        info(f"Fetching repository version {package_version} for {package_name} at {package_repository}")

        # fetch minimal info from repo with filter and depth 1 
        exec_shell(f"git fetch --depth 1 --filter=blob:none origin {package_version}")
        exec_shell("git sparse-checkout init --cone")
        exec_shell("git checkout FETCH_HEAD")

        yacpkg["^current_version"] = package_version

    # get lists of includes from the yacpm.json package declaration or yacpkg.json and combine them
    # note that these includes can be either string or array
    sparse_checkout_array: list[str] = ensure_array(yacpkg.get("include", []))
    if not info_is_str:
        sparse_checkout_array += ensure_array(package_info.get("include", []))
    sparse_checkout_list = " ".join(sparse_checkout_array)

    # git sparse checkout list will download only the necessery directories of the repository
    if sparse_checkout_list and yacpkg.get("^sparse_checkout_list") != sparse_checkout_list:
        info(f"Fetching directories {','.join(sparse_checkout_array)} for package {package_name}")

        exec_shell(f"git sparse-checkout set {sparse_checkout_list}")
        yacpkg["^sparse_checkout_list"] = sparse_checkout_list

    yacpkg_file.seek(0)
    json.dump(yacpkg, yacpkg_file, ensure_ascii=False, indent=4)

    os.chdir(project_dir)

package_names = yacpm["packages"].keys()

include_file_output = ""
for name in package_names:
    include_file_output += f"add_subdirectory(${{CMAKE_CURRENT_SOURCE_DIR}}/yacpkgs/{name})\n"

include_file_output += f"set(YACPM_LIBS {' '.join(package_names)})"

include_file = open("yacpkgs/packages.cmake", "w")
include_file.write(include_file_output)
