import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from yacpm import YACPM_BRANCH, info

yacpm = { "packages": {}, "remote": "../../packages" }

for directory in next(os.walk("../../packages/"))[1]:
    info(f"Getting default branch for {directory}")
    yacpkg = json.load(open(f"../../packages/{directory}/yacpkg.json"))
    proc = subprocess.run(f"git remote show {yacpkg['repository']}", shell=True, stdout=subprocess.PIPE)
    default_branch = re.findall("(?<=HEAD branch: ).+", proc.stdout.decode("utf-8"))[0]

    yacpm["packages"][directory] = default_branch

file = open("yacpm.json", "w")
json.dump(yacpm, file, ensure_ascii=False, indent=4)
