#!/usr/bin/env python3

#
# Run tests (specfied by cli arguments), or all if unspecified, with a
# directory from this directory. This script will copy the script files in the
# current working tree so the latest changes will be tested.
#

import os
import sys
import shutil
import multiprocessing

current_dir = os.getcwd()
tests_dir = os.path.dirname(os.path.abspath(__file__))

# cli args or directories of this python file's directory (the tests directory)
tests_dirs = sys.argv[1:] or next(os.walk(tests_dir))[1]

for test_dir in tests_dirs:
    print(f"\nRUNNING TEST: {test_dir}\n")

    if not os.path.isdir(test_dir):
        print(f"{test_dir} is not a directory!")
        exit()
    
    build_dir = f"{test_dir}/build"
    if not os.path.isdir(build_dir):
        os.makedir(build_dir)

    os.chdir(build_dir)
    shutil.copy(f"{tests_dir}/../yacpm.cmake", "./")
    shutil.copy(f"{tests_dir}/../yacpm.py", "./")

    if not os.path.exists("./Makefile"):
        os.system("cmake ..")

    os.system(f"make -j{multiprocessing.cpu_count()}")
    os.chdir(current_dir)

