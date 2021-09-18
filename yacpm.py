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

def error(msg: str):
    print(f"==== YACPM ERROR: {msg}", file=sys.stderr)
    exit(1)

def download_not_exist(url: str, outfile: str):
    if not os.path.isfile(outfile):
        urllib.request.urlretrieve(url, outfile)

def exec_shell(command: str):
    proc = subprocess.run(command, shell=True, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        error(proc.stderr.decode("utf-8"))

def info(msg: str):
    # normal printing doesn't update realtime with cmake
    exec_shell(f"python -c \"print ('==== {msg}')\"")

def ensure_array(value):
    return value if isinstance(value, list) else [value]

if not "packages" in yacpm or not isinstance(yacpm["packages"], dict):
    error("Expected yacpm.json to have a packages field that is an object!")

for package_name, package_info in yacpm["packages"].items():
    # make directories
    output_dir = f"yacpkgs/{package_name}"
    os.makedirs(output_dir, exist_ok=True)
    os.chdir(output_dir)

    info(f"Fetching package {package_name}...")

    # download package info
    try:
        package_url = f"{remote_url}/{package_name}"
        download_not_exist(f"{package_url}/CMakeLists.txt", "CMakeLists.txt")
        download_not_exist(f"{package_url}/yacpkg.json", "yacpkg.json")
    except urllib.error.HTTPError as err:
        if err.code == 404:
            error(f"{package_name} was not found on remote {remote_url}")
        else:
            raise

    yacpkg_file = open("yacpkg.json", "r+")
    yacpkg = json.load(yacpkg_file)
    info_is_version = isinstance(package_info, str) # just a simple tag/commit/branch
    package_version = package_info if info_is_version else package_info["version"];

    # all keys with ^ at the front was created by this script
    if yacpkg.get("^current_version", "") != package_version:
        if os.path.isdir("repository"):
            shutil.rmtree("repository")

        # setup git repository using sparse checkout to only fetch required directories
        exec_shell("git init repository")
        os.chdir("repository")
        exec_shell(f"git remote add origin {yacpkg['repository']}")
        
        exec_shell(f"git fetch --depth 1 --filter=blob:none origin {package_version}")
        exec_shell("git sparse-checkout init --cone")
        exec_shell("git checkout FETCH_HEAD")
        yacpkg["^current_version"] = package_version
    else:
        os.chdir("repository")

    sparse_checkout_array = ensure_array(yacpkg.get("include", []))
    if not info_is_version:
        sparse_checkout_array += ensure_array(package_info.get("include", []))
    sparse_checkout_list = " ".join(sparse_checkout_array)

    if yacpkg.get("^sparse_checkout_list", "") != sparse_checkout_list:
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

