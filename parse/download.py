#!/usr/bin/python

import argparse
import subprocess
from pprint import pprint
from pathlib import Path
import json
import logging
from util import *
from multiprocessing import Pool
from packaging import version as Version

logging.basicConfig(level=logging.DEBUG)

parser = argparse.ArgumentParser(
    prog="download.py",
    description="download and prepare kernel source for parsing",
)
parser.add_argument("--tag", help="kernel tag", required=True)
parser.add_argument("--static", help="static file directory", default="static")
parser.add_argument("--git-url", help="git provider", default="https://github.com/torvalds/linux")
parser.add_argument("-j", help="number of processes", default=4, type=int)
# parser.add_argument("action", choices=["--debug", "--info"])

args = parser.parse_args()
processes = args.j
version = args.tag
static = Path(args.static)
static.mkdir(exist_ok=True)
cache = Path("cache")
cache.mkdir(exist_ok=True)
bucket = cache / version
bucket.mkdir(exist_ok=True)
json_dir = static / version
json_dir.mkdir(exist_ok=True)
linux = bucket / "linux"
version_file = static / "versions.json"
archlist_cache = json_dir / "archlist.json"

def install(arch: str):
    try:
        headers = bucket / "headers" / arch
        if not headers.exists():
            subprocess.run(f"make headers_install INSTALL_HDR_PATH='{headers.absolute()}' ARCH='{arch}'", shell=True, cwd=linux, check=True)
        else:
            logging.warning(f"{headers} already exists, not installing")
        return True
    except subprocess.CalledProcessError as e:
        logging.warning(f"failed to build headers for {arch}")
        return False

if not linux.exists():
    subprocess.run(f"git clone --depth 1 --branch '{args.tag}' '{args.git_url}' '{linux}'", shell=True, check=True)
    subprocess.run(f"make defconfig", shell=True, cwd=linux, check=True)
else:
    logging.warning(f"{cache} already exists, not downloading")

if archlist_cache.exists():
    with open(archlist_cache, "r") as f:
        archlist = json.load(f)
else:
    archlist = Path(linux / "arch").glob("*/")
    archlist = [path.stem for path in archlist]

working = []

for arch in archlist:
    if install(arch):
        working.append(arch)

with open(archlist_cache, "w+") as f:
    f.write(json.dumps(working))

if version_file.exists():
    with open(static / "versions.json", "r") as f:
        versions = json.load(f)
else:
    versions = {}

major = Version.parse(version).major
major = f"v{major}"
versions.setdefault(major, []).append(version)
versions[major] = list(set(versions[major]))
versions[major].sort(key=lambda verstr: Version.parse(verstr), reverse=True)
versions = dict(sorted(versions.items(), key=lambda item: Version.parse(item[0]), reverse=True))

with open(static / "versions.json", "w+") as f:
    f.write(json.dumps(versions))