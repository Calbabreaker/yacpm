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

YACPM_BRANCH = "v3"

# Do not touch YACPM_BRANCH or merge conflict will happen
PROJECT_DIR = os.getcwd()
VERBOSE = False


# Utility functions
def error(msg: str, print_wrapper: bool = True):
    text = f"==== YACPM ERROR: {msg}" if print_wrapper else msg
    print(text, file=sys.stderr)
    exit(1)


def info(msg: str, print_wrapper: bool = True):
    msg = msg.strip()
    text = f"==== {msg}" if print_wrapper else msg
    # Print by spawning python as normal printing doesn't update realtime with cmake
    subprocess.run([sys.executable, "-c", f"print('''{text}''')"])


def open_read_write(filename: str, is_json: bool = False) -> Tuple[TextIOWrapper, Any]:
    file = open(filename, "r+")
    content = json.load(file) if is_json else file.read()
    file.seek(0)
    return (file, content)


def write_json(data: dict, file: TextIOWrapper):
    json.dump(data, file, indent=4)
    file.truncate()
    file.close()


def write_packages_cmake(package_names: list[str]):
    if not os.path.exists("yacpkgs"):
        os.mkdir("yacpkgs")
    cmake_output = f"set(YACPM_PACKAGES {' '.join(package_names)})\n"
    cmake_output += "foreach(PACKAGE ${YACPM_PACKAGES})\n"
    cmake_output += "    if(NOT TARGET ${PACKAGE})\n"
    cmake_output += "        add_subdirectory(${YACPM_DIR}/yacpkgs/${PACKAGE} yacpkgs/${PACKAGE})\n"
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


def exec_shell(command_args: list[str], verbose=VERBOSE) -> str:
    command_str = ' '.join(command_args)
    if verbose:
        info(f"> {command_str}", False)

    proc = subprocess.run(
        command_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout = proc.stdout.decode("utf-8")

    if verbose and stdout:
        info(stdout, False)

    if proc.returncode != 0:
        error(
            f"Failed to run '{command_str}': \n{proc.stderr.decode('utf-8')}")

    return stdout


def dict_merge(out: dict, input: dict):
    for key, value in input.items():
        out_value = out.get(key)

        if isinstance(value, set):
            # Convert set to list
            out[key] = list(value)
        elif value and not out_value:
            # Only merge values if out dict doesn't have the key
            out[key] = value
        elif isinstance(value, list) and isinstance(out_value, list):
            out_value[0:0] = value
        elif isinstance(value, dict) and isinstance(out_value, dict):
            dict_merge(out_value, value)


def ensure_package_is_dict(package_info: Union[dict, str]) -> dict:
    if not isinstance(package_info, dict):
        return {"version": package_info}
    else:
        return package_info


# Main functions
def parse_package_version(package_version: str) -> str:
    git_ref = package_version.replace("+", "")
    # Get default branch if no version specifed
    if git_ref == "":
        result = exec_shell(["git", "remote", "show", "origin"])
        git_ref = re.findall("(?<=HEAD branch: ).+", result)[0]

    # Fetch repo with least amount of downloading
    exec_shell(["git", "fetch", "--depth=1",
               "--filter=blob:none", "origin", git_ref])
    exec_shell(["git", "sparse-checkout", "init"])
    exec_shell(["git", "checkout", "FETCH_HEAD"])

    # Don't freeze to commit if version starting with +
    if not package_version.startswith("+"):
        rev_name = exec_shell(["git", "name-rev", "HEAD"]).strip()
        # Version is a branch then convert to commit
        if not rev_name.endswith("undefined"):
            package_version = exec_shell(["git", "rev-parse", "HEAD"]).strip()
    # Don't set default branch if it's ++
    elif package_version != "++":
        package_version = "+" + git_ref

    return package_version


def download_package_metadata(remotes: list[str], package_name: str) -> Union[str, None]:
    """Downloads the package metadata from a list of remotes
    Each remote should be a directory that contains a list of package names
    Returns remote that was downloaded from (if actually did download)"""

    for remote in remotes:
        if remote == "DEFAULT_REMOTE":
            remote = f"https://github.com/Calbabreaker/yacpm/raw/{YACPM_BRANCH}/packages"

        package_path = f"{remote}/{package_name}"
        try:
            did_download = download_if_missing(
                f"{package_path}/yacpkg.json", "yacpkg.json")
            did_download = download_if_missing(
                f"{package_path}/CMakeLists.txt", "CMakeLists-downloaded.txt")
        except (urllib.error.HTTPError, FileNotFoundError) as err:
            if isinstance(err, FileNotFoundError) or err.code == 404:
                # try next remote if fail to download
                continue
            else:
                raise

        # else return successfully
        return remote if did_download else None

    error(f"{package_name} was not found on any of these remotes: {', '.join(remotes)}")


def generate_cmake_variables(package_info: dict) -> str:
    cmake_output = ""
    if package_info.get("variables"):
        for variable, value in package_info["variables"].items():
            if isinstance(value, bool):
                value = "ON" if value else "OFF"
                type_str = "BOOL"
            elif isinstance(value, str):
                value = f'"{value}"'
                type_str = "STRING"
            else:
                error("{variable} needs to be a string or boolean")

            if variable == "BUILD_SHARED_LIBS" or variable == "CMAKE_BUILD_TYPE":
                cmake_output += f"set({variable} {value})\n"
            else:
                cmake_output += f'set({variable} {value} CACHE {type_str} "" FORCE)\n'
    return cmake_output


def download_package_files(yacpkg: dict, package_info: Union[dict, str], progress_print: str):
    """Calc sparse checkout list and download the neccessery package files"""

    # Get lists of includes from the yacpm.json package declaration and yacpkg.json package config and combines them
    sparse_checkout_list: list[str] = yacpkg.get("include", []).copy()
    if isinstance(package_info, dict):
        sparse_checkout_list += package_info.get("include", [])

    if yacpkg.get("^sparse_checkout_list") != sparse_checkout_list:
        info(progress_print)
        exec_shell(["git", "sparse-checkout", "set",
                   "--no-cone"] + sparse_checkout_list)
        yacpkg["^sparse_checkout_list"] = sparse_checkout_list


def get_package_dependencies(all_packages: dict, remotes: list, next_iter_package_names: set, dependent_name: str):
    """Gets all packages config inside current directory yacpm.json and combine it with the config
    in the all_packages dict to make sure they are accounted for when fetching the specific dependency package
    """
    yacpm_config = json.load(open("yacpm.json"))

    package_list: dict = yacpm_config["packages"]
    package_list.update(yacpm_config.get("dependency_packages", {}))

    for package_name, package_info in package_list.items():
        root_package = all_packages.get(package_name, {})
        # Make sure all_packages contains the package dict if it was set
        all_packages[package_name] = root_package

        package_info = ensure_package_is_dict(package_info)
        dict_merge(root_package, package_info)

        # Convert to sets to ensure no duplicate dependent names
        dependents = root_package.get("dependents", [])
        if not isinstance(dependents, set):
            root_package["dependents"] = set(dependents)
            root_package["dependents_left"] = set(dependents)

        root_package["dependents"].add(dependent_name)
        root_package["dependents_left"].discard(dependent_name)

    # Prepend to remotes to give the package remotes piority
    remotes[0:0] = yacpm_config.get("remotes", [])

    package_names = package_list.keys()
    next_iter_package_names.update(package_names)
    write_packages_cmake(package_names)


def get_packages(package_names, all_packages: dict, remotes: list):
    next_iter_package_names = set()

    for i, package_name in enumerate(package_names):
        package_info = ensure_package_is_dict(all_packages[package_name])
        all_packages[package_name] = package_info

        # Skip if haven't parsed fetched all dependents yet
        if package_info.get("dependents_left"):
            continue

        progress_indicator = f"[{i + 1}/{len(package_names)}]"

        output_dir = f"yacpkgs/{package_name}"
        # Make the package output dir (repository dir as well for later use)
        os.makedirs(f"{output_dir}/repository", exist_ok=True)
        os.chdir(output_dir)

        package_version = package_info.get("version")
        if not isinstance(package_version, str):
            error(
                f"Expected package {package_name} to have a version field or be a string that is the version")

        package_repository = package_info.get("repository")
        specified_cmake_file = package_info.get("cmake")

        if specified_cmake_file:
            download_if_missing(specified_cmake_file,
                                "CMakeLists-downloaded.txt")

        # If the user didn't specify both the package repo and CMakeLists then we have to download the package metadata
        if not specified_cmake_file or not package_repository:
            remote_used = download_package_metadata(remotes, package_name)
            if remote_used:
                info(
                    f"{progress_indicator} Downloaded {package_name} package metadata from {remote_used}")

        # If didn't download yacpkg.json file then create it
        if not os.path.exists("yacpkg.json"):
            open("yacpkg.json", "w").write("{}")
        yacpkg_file, yacpkg = open_read_write("yacpkg.json", True)

        os.chdir("repository")

        # If user didn't specify repository
        package_repository = package_repository or yacpkg["repository"]

        # Initialize git repository
        if not os.path.exists(".git"):
            exec_shell(["git", "init"])
            exec_shell(["git", "remote", "add", "origin", package_repository])
            yacpkg["^current_version"] = None

        # Freeze package versions to use commit hashes
        if yacpkg.get("^current_version") != package_version:
            info(
                f"{progress_indicator} Fetching {package_name}@{package_version} from {package_repository}")
            package_version = parse_package_version(package_version)

            package_info["version"] = package_version

            yacpkg["^current_version"] = package_version
            yacpkg["^sparse_checkout_list"] = ""  # Force recheck fetch files

        # Generate cmake for variables and prepend that onto the download CMakeLists.txt
        prepend_cmake = generate_cmake_variables(package_info)
        cmake_lists_content = open("../CMakeLists-downloaded.txt").read()
        open("../CMakeLists.txt", "w").write(prepend_cmake + cmake_lists_content)

        download_print = f"{progress_indicator} Downloading files for {package_name}"
        download_package_files(yacpkg, package_info, download_print)
        write_json(yacpkg, yacpkg_file)

        # Make sure to potential yacpm config inside the yacpkg.json
        if "packages" in yacpkg:
            json.dump({"packages": yacpkg["packages"]}, open(
                "yacpm.json", "w"))

        # Run potential yacpm.json inside the fetched package
        if os.path.isfile("yacpm.json"):
            get_package_dependencies(
                all_packages, remotes, next_iter_package_names, package_name)

        os.chdir(PROJECT_DIR)

    # Get the dependency packages found in this iteration
    if next_iter_package_names:
        info(f"Calculating dependencies: {', '.join(next_iter_package_names)}")
        get_packages(next_iter_package_names, all_packages, remotes)


def update_package_info(all_packages: dict, dependency_packages: dict, package_list: dict):
    """Update dependency_packages and normal package_list from the all_packages dict depending on
    if the pacakage is a dependency of another package"""

    for package_name, package_info in all_packages.items():
        dependents = ensure_package_is_dict(package_info).get("dependents")
        if not dependents:
            # If the package list in the yacpm.json file is just a version string, keep it that way
            if isinstance(package_list[package_name], str):
                package_list[package_name] = package_info["version"]
            else:
                package_list[package_name] = package_info
            continue

        # If no package depends on this package move it back to normal package list
        if len(dependents) == 0 or not isinstance(dependents, set):
            package_list[package_name] = dependency_packages[package_name]
            package_list[package_name].pop("dependents")
            dependency_packages.pop(package_name)
            continue

        # Move package from normal packages list to dependency packages list
        if package_name in package_list:
            dependency_packages[package_name] = package_list[package_name]
            package_list.pop(package_name)

        # Remove missing dependents
        if isinstance(dependents, set):
            dependents.difference_update(package_info["dependents_left"])

        package_info.pop("dependents_left")
        if "include" in package_info:
            package_info.pop("include")

        dependency_packages[package_name] = ensure_package_is_dict(
            dependency_packages.get(package_name))
        dict_merge(dependency_packages[package_name], package_info)


if __name__ == "__main__":
    # Load yacpm.json
    yacpm_file, yacpm = open_read_write("yacpm.json", True)
    VERBOSE = yacpm.get("verbose")

    package_list: dict = yacpm["packages"]
    remotes = yacpm.get("remotes", ["DEFAULT_REMOTE"])
    dependency_packages = yacpm.get("dependency_packages", {})
    all_packages = deepcopy(package_list)
    all_packages.update(deepcopy(dependency_packages))
    get_packages(package_list.keys(), all_packages, remotes)

    update_package_info(all_packages, dependency_packages, package_list)
    if dependency_packages and "dependency_packages" not in yacpm:
        yacpm["dependency_packages"] = dependency_packages

    write_json(yacpm, yacpm_file)

    # Prune unused packages in yacpkgs
    for directory in next(os.walk("yacpkgs"))[1]:
        if directory not in all_packages:
            info(f"Removing unused package {directory}")
            shutil.rmtree(f"yacpkgs/{directory}")

    write_packages_cmake(package_list.keys())
