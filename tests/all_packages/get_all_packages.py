import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from yacpm import info, open_read_write, write_json

if not os.path.exists("yacpm.json"):
    open("yacpm.json", "w").write('{ "packages": {}, "remote": "../../packages" }')

file, yacpm = open_read_write("yacpm.json", True)

for directory in next(os.walk("../../packages/"))[1]:
    if directory in yacpm["packages"]:
        continue

    info(f"Getting default branch for {directory}")
    yacpkg = json.load(open(f"../../packages/{directory}/yacpkg.json"))
    proc = subprocess.run(f"git remote show {yacpkg['repository']}", shell=True, stdout=subprocess.PIPE)
    default_branch = re.findall("(?<=HEAD branch: ).+", proc.stdout.decode("utf-8"))[0]

    yacpm["packages"][directory] = default_branch

write_json(yacpm, file)
