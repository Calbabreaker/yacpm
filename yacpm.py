#!/usr/bin/env python3

#
# Python script that parses a yacpm.json and downloads necessery libraries into
# yapkgs/ directory.
#

import json
import os
import urllib.request
import urllib.error

YACPM_BRANCH = "main"

project_dir = os.getcwd()
yacpm = json.load(open("yacpm.json"))
remote_url = yacpm.get("remote", "https://raw.githubusercontent.com/Calbabreaker/yacpm/{YACPM_BRANCH}/packages")

def error(msg: str):
    print(f"==== {msg} ====")
    exit(1)

def download_not_exist(url: str, outfile: str):
    if not os.path.isfile(outfile):
        urllib.request.urlretrieve(url, outfile)


for package_name, package_info in yacpm["packages"].items():
    # make directories
    output_dir = f"yapkgs/{package_name}"
    os.makedirs(output_dir, exist_ok=True)
    os.chdir(output_dir)

    # download package info
    try:
        package_url = f"{remote_url}/{package_name}"
        download_not_exist(f"{package_url}/CMakeLists.txt", "CMakeLists.txt")
        download_not_exist(f"{package_url}/yacpkg.json", "yacpkg.json")
    except urllib.error.HTTPError as err:
        if err.code == 404:
            error(f"YACPM ERROR: {package_name} was not found on remote {remote_url}")
        else:
            raise

    yacpkg = json.load(open("yacpkg.json"))
    info_is_version = isinstance(package_info, str) # just a simple tag/commit/branch
    package_version = package_info if info_is_version else package_info.version;

    # ^current_version key was created by this script
    if yacpkg["^current_version"] != package_version:

        # setup git repository using sparse checkout to only fetch required directories
        os.system("git init repository")
        os.chdir("repository")
        os.system(f"git remote add origin {yacpkg['repository']}")
        
        os.system(f"git fetch --depth 1 --filter=blob:none {package_version}")
        os.system("git sparse-checkout init --cone")
        os.system("git checkout FETCH_HEAD")

        sparse_checkout_list = ""
        sparse_checkout_list += " ".join(yacpkg.include)
        if not info_is_version:
            sparse_checkout_list += " ".join(package_info.include)
        os.system(f"git sparse-checkout set {sparse_checkout_list}")

    os.chdir(project_dir)

