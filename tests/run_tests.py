#!/usr/bin/env python3

#
# Run tests (specfied by cli arguments), or all if unspecified, with a
# directory from this directory. This script will symlink the script files in the
# current working tree so the latest changes will be tested.
#

import multiprocessing
import os
import sys
from argparse import ArgumentParser

# import files from previous directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from yacpm import info, exec_shell

tests_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(tests_dir)

parser = ArgumentParser(description="Run tests from tests/ directory")
parser.add_argument("tests", type=str, nargs="*", 
                    help="A list of tests. Default is all of them in the tests/ directory.", 
                    default=next(os.walk(tests_dir))[1])
parser.add_argument("-n", "--no-run", dest="run", action="store_false",
                    help="Don't run the output executable (just build).")

args = parser.parse_args()

def symlink(src, dest):
    if not os.path.exists(dest):
        os.symlink(src, dest)

for test_dir in args.tests:
    print_text = f"== RUNNING TEST: {test_dir} =="
    padding = "=" * len(print_text)

    # Github actions doesn't print this here if using print()
    info("", False)
    info(padding, False)
    info(print_text, False)
    info(padding, False)

    if not os.path.exists(test_dir):
        print(f"{test_dir} is not a directory in tests!")
        exit(1)
    
    build_dir = f"{test_dir}/build"
    if not os.path.exists(build_dir):
        os.mkdir(build_dir)

    os.chdir(build_dir)
    symlink(f"{tests_dir}/../yacpm.cmake", "yacpm.cmake")
    symlink(f"{tests_dir}/../yacpm_extended.cmake", f"yacpm_extended.cmake")
    symlink(f"{tests_dir}/../yacpm.py", f"yacpm.py")

    exec_shell(["cmake", ".."], True)
    exec_shell(["cmake", "--build", os.getcwd(), "--parallel", str(multiprocessing.cpu_count())], True)

    if not args.run:
        continue

    # find the executable and execute it
    for executable in os.listdir("./bin"):
        info(f"Running {executable}..", False)
        os.chdir("../")

        try:
            exec_shell([f"{os.getcwd()}/build/bin/{executable}"], True)
        except PermissionError:
            pass

    os.chdir(tests_dir)

