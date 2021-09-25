#!/usr/bin/env python3

#
# Run tests (specfied by cli arguments), or all if unspecified, with a
# directory from this directory. This script will copy the script files in the
# current working tree so the latest changes will be tested.
#

import multiprocessing
import os
import shutil
import stat
import subprocess
import sys
from argparse import ArgumentParser

# import files from previous directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from yacpm import YACPM_BRANCH

tests_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(tests_dir)

parser = ArgumentParser(description="Run tests from tests/ directory")
parser.add_argument("tests", type=str, nargs="*", 
                    help="A list of tests. Default is all of them in the tests/ directory.", 
                    default=next(os.walk(tests_dir))[1])
parser.add_argument("-t", "--timeout", dest="timeout", type=int, 
                    help="How long to kill the executable process after ran and hasn't stopped.")
parser.add_argument("-n", "--no-run", dest="run", action="store_false",
                    help="Don't run the output executable (just build).")

args = parser.parse_args()

def copy_file(src, dest):
    if os.path.exists(dest):
        os.remove(dest)
    shutil.copyfile(src, dest)

def exec_shell(cmd):
    if os.system(cmd) != 0:
        exit()

for test_dir in args.tests:
    print(f"=== RUNNING TEST: {test_dir} === \n")

    if not os.path.isdir(test_dir):
        print(f"{test_dir} is not a directory in tests!")
        exit()
    
    build_dir = f"{test_dir}/build"
    if not os.path.isdir(build_dir):
        os.mkdir(build_dir)

    os.chdir(build_dir)
    copy_file(f"{tests_dir}/../yacpm.cmake", "yacpm.cmake")
    copy_file(f"{tests_dir}/../yacpm_extended.cmake", f"yacpm_extended-{YACPM_BRANCH}.cmake")
    copy_file(f"{tests_dir}/../yacpm.py", f"yacpm-{YACPM_BRANCH}.py")

    if not os.path.exists("./Makefile"):
        exec_shell("cmake ..")

    exec_shell(f"make -j{multiprocessing.cpu_count()}")

    if not args.run:
        continue

    # find the executable and execute it
    executable_flag = stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH
    for filename in next(os.walk("./"))[2]:
        mode = os.stat(filename).st_mode
        if mode & executable_flag:
            process = subprocess.Popen([f"./{filename}"])
            try:
                process.wait(args.timeout)
            except subprocess.TimeoutExpired:
                process.terminate()
    
    os.chdir(tests_dir)

