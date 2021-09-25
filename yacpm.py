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

# utility functions
def get_includes(dictionary):
    value = dictionary.get("include", [])
    return value if isinstance(value, list) else [value]

def error(msg: str, print_wrapper: bool = True):
    text = f"==== YACPM ERROR: {msg}" if print_wrapper else msg 
    print(text, file=sys.stderr)
    exit(1)

def info(msg: str):
    # normal printing doesn't update realtime with cmake
    os.system(f"python -c 'print (\"==== {msg}\")'")

if __name__ == "__main__":
    # load yacpm.json
    project_dir = os.getcwd()
    yacpm = json.load(open("yacpm.json"))
    remote_url: str = yacpm.get("remote", f"https://raw.githubusercontent.com/Calbabreaker/yacpm/{YACPM_BRANCH}/packages")

    def download_not_exist(url: str, outfile: str):
        if not os.path.exists(outfile):
            info(f"Downloading {url}...")
            if remote_url.startswith("http"):
                urllib.request.urlretrieve(url, outfile)
            else:
                shutil.copyfile(f"{project_dir}/{url}", outfile)

    def exec_shell(command: str, return_result: bool = False):
        if yacpm.get("verbose") and not return_result:
            info(command)
            if os.system(command) != 0:
                exit(1)
        else:
            proc = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # errors are not silented
            if proc.returncode != 0:
                error(proc.stderr.decode("utf-8"), False)
            if return_result:
                return proc.stdout.decode("utf-8")

    if not "packages" in yacpm or not isinstance(yacpm["packages"], dict):
        error("Expected yacpm.json to have a packages field that is an object!")

    include_file_output = ""

    for package_name, package_info in yacpm["packages"].items():
        # check if package info a object containing the version field or it's the version as a string 
        info_is_str = isinstance(package_info, str) 
        package_version = package_info if info_is_str else package_info["version"] 

        output_dir = f"yacpkgs/{package_name}-{YACPM_BRANCH}-{package_version}"
        package_url = f"{remote_url}/{package_name}"

        # make directories
        os.makedirs(f"{output_dir}/repository", exist_ok=True) # make the repository dir as well for later use
        os.chdir(output_dir)

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

        yacpkg_file = open("yacpkg.json", "r+")
        yacpkg = json.load(yacpkg_file)

        package_repository = package_repository or yacpkg["repository"]
        os.chdir("repository")

        # initialize git repository
        if not os.path.exists(".git"):
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

            if specified_cmake_file == None and os.path.exists("../CMakeLists.txt"):
                os.remove("../CMakeLists.txt")

            yacpkg["^current_version"] = package_version

        # find matching CMakeLists.txt or includes by comparing unix timestamps
        commit_timestamp = exec_shell("git show -s --format=%ct", return_result=True)
        package_config = None
        if "configs" in yacpkg:
            timestamps = list(yacpkg["configs"].keys())

            for i in range(len(timestamps)):
                if len(timestamps) == i + 1 or commit_timestamp < timestamps[i + 1]:

                    config = yacpkg["configs"].get(timestamps[i], None)
                    if config == None:
                        error(f"Package {package_name} at {package_version} is not supported!")
                    if "cmake" in config:
                        download_not_exist(f"{package_url}/{config['cmake']}", "../CMakeLists.txt")

                    package_config = config
                    info(package_config)
                    break

        # if there are no configs or no explictly specifed CMakeLists.txt, download the default one
        download_not_exist(f"{package_url}/CMakeLists.txt", "../CMakeLists.txt")

        # get lists of includes from the yacpm.json package declaration or yacpkg.json package config and combine them
        # note that these includes can be either string or array
        sparse_checkout_array: list[str] = get_includes(yacpkg)
        if not info_is_str:
            sparse_checkout_array += get_includes(package_info)
        if package_config != None:
            sparse_checkout_array += get_includes(package_config)
        sparse_checkout_list = " ".join(sparse_checkout_array)

        # git sparse checkout list will download only the necessery directories of the repository
        if sparse_checkout_list and yacpkg.get("^sparse_checkout_list") != sparse_checkout_list:
            info(f"Fetching directories {','.join(sparse_checkout_array)} for package {package_name}")

            exec_shell(f"git sparse-checkout set {sparse_checkout_list}")
            yacpkg["^sparse_checkout_list"] = sparse_checkout_list

        yacpkg_file.seek(0)
        json.dump(yacpkg, yacpkg_file, ensure_ascii=False, indent=4)

        include_file_output += f"add_subdirectory(${{CMAKE_SOURCE_DIR}}/{output_dir})\n"

        os.chdir(project_dir)

    package_names = yacpm["packages"].keys()
    include_file_output += f"set(YACPM_LIBS {' '.join(package_names)})"

    include_file = open("yacpkgs/packages.cmake", "w")
    include_file.write(include_file_output)