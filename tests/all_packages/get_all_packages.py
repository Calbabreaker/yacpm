import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from yacpm import open_read_write, write_json

# packages that conflict with others (contain cmake targets inside)
conflicting_packages = {"raylib"}

def touch_yacpm(filepath):
    if not os.path.exists(filepath):
        open(filepath, "w").write('{ "packages": {}, "remote": "../../packages" }')

touch_yacpm("yacpm.json")
touch_yacpm("conflicting/yacpm.json")

json_file, yacpm = open_read_write("yacpm.json", True)
conflicting_json_file, conflicting_yacpm = open_read_write("conflicting/yacpm.json", True)

for directory in next(os.walk("../../packages/"))[1]:
    if directory in yacpm["packages"]:
        continue

    if directory in conflicting_packages:
        conflicting_yacpm["packages"][directory] = ""
        continue

    yacpm["packages"][directory] = ""

write_json(yacpm, json_file)
write_json(conflicting_yacpm, conflicting_json_file)
