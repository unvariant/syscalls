from util import *
import re
import logging
from pprint import pprint, pformat
from pathlib import Path

class Target:
    def __init__(self, arch: str, abi: str):
        self.arch = arch
        self.abi = abi