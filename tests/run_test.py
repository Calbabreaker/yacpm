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
import sys

tests_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(tests_dir)

# cli args or directories of this python file's directory (the tests directory)
tests_dirs = sys.argv[1:] or next(os.walk(tests_dir))[1]

def copy_here(src):
    filename = os.path.basename(src)
    if os.path.exists(filename):
        os.remove(filename)
    shutil.copyfile(src, filename)

def exec_shell(cmd):
    if os.system(cmd) != 0:
        exit()

for test_dir in tests_dirs:
    print(f"=== RUNNING TEST: {test_dir} === \n")

    if not os.path.isdir(test_dir):
        print(f"{test_dir} is not a directory!")
        exit()
    
    build_dir = f"{test_dir}/build"
    if not os.path.isdir(build_dir):
        os.mkdir(build_dir)

    os.chdir(build_dir)
    copy_here(f"{tests_dir}/../yacpm.cmake")
    copy_here(f"{tests_dir}/../yacpm.py")

    if not os.path.exists("./Makefile"):
        exec_shell("cmake ..")

    exec_shell(f"make -j{multiprocessing.cpu_count()}")

    # find the executable and execute it
    executable_flag = stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH
    for filename in next(os.walk("./"))[2]:
        mode = os.stat(filename).st_mode
        if mode & executable_flag:
            os.system(f"./{filename}")
    
    os.chdir(tests_dir)

