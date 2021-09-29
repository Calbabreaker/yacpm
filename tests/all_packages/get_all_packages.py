import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from yacpm import open_read_write, write_json

if not os.path.exists("yacpm.json"):
    open("yacpm.json", "w").write('{ "packages": {}, "remote": "../../packages" }')

file, yacpm = open_read_write("yacpm.json", True)

for directory in next(os.walk("../../packages/"))[1]:
    if directory in yacpm["packages"]:
        continue

    yacpm["packages"][directory] = ""

write_json(yacpm, file)
