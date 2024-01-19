#!/usr/bin/python

import argparse
import subprocess
from pprint import pprint
from pathlib import Path
import json
import logging
from util import *
from multiprocessing import Pool
import errno

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
static = Path(args.static)
static.mkdir(exist_ok=True)
cache = Path("cache")
cache.mkdir(exist_ok=True)
bucket = cache / args.tag
bucket.mkdir(exist_ok=True)
json_dir = bucket / "json"
json_dir.mkdir(exist_ok=True)
linux = bucket / "linux"

def install(arch: str):
    headers = bucket / "headers" / arch
    if not headers.exists():
        subprocess.run(f"make defconfig ARCH='{arch}'", shell=True, cwd=linux, check=True)
        subprocess.run(f"make headers_install INSTALL_HDR_PATH='{headers.absolute()}' ARCH='{arch}'", shell=True, cwd=linux, check=True)
    else:
        logging.warning(f"{headers} already exists, not installing")

if not linux.exists():
    subprocess.run(f"git clone --depth 1 --branch '{args.tag}' '{args.git_url}' '{linux}'", shell=True, check=True)
else:
    logging.warning(f"{cache} already exists, not downloading")

archlist = Path(linux / "arch").glob("*/")
archlist = [path.stem for path in archlist]

working = []

for arch in archlist:
    try:
        result = install(arch)
        working.append(arch)
    except subprocess.CalledProcessError as e:
        logging.warning(f"failed to build headers for {arch}")

with open(json_dir / "archlist.json", "w+") as f:
    f.write(json.dumps(working))