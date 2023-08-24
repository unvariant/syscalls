#!/usr/bin/python

import argparse
from signatures import Signatures
from constraints import Constraints
from pprint import pprint
from pathlib import Path
import json
import logging

logging.basicConfig(level=logging.INFO)

parser = argparse.ArgumentParser(
    prog="parse.py",
    description="parse kernel source for syscall definitions",
)
parser.add_argument("--static", help="static file directory", required=True)
parser.add_argument("--tag", help="kernel tag", required=True)
# parser.add_argument("action", choices=["signatures", "constraints"])
args = parser.parse_args()

static = Path(args.static).absolute()
static.mkdir(exist_ok=True)
json_dir = static / "json"
json_dir.mkdir(exist_ok=True)
cache = Path("cache").absolute() / args.tag

if not cache.exists():
    logging.error(f"cache directory {cache} does not exist")
    exit(1)

signatures = Signatures(cache)
signatures.generate()
constraints = Constraints(cache, json_dir, signatures)
archinfo = constraints.generate()
with open(json_dir / "info.json", "w+") as f:
    json.dump(archinfo, f)