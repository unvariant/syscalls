#!/usr/bin/python

import argparse
from signatures import Signatures
from pprint import pprint

parser = argparse.ArgumentParser(
    prog="parse.py",
    description="parse kernel source for syscall definitions", )
parser.add_argument("action", choices=["signatures"])
args = parser.parse_args()

match args.action:
    case "signatures":
        signatures = Signatures("cache/v6.5-rc6/")
        pprint(signatures.specific["x86"])
        pprint(signatures.syscall("x86", "exit"))