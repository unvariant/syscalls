from pathlib import Path
from typing import *
import subprocess

def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, encoding="utf-8")

def grouppairs(iterable: Iterable):
    a = iter(iterable)
    return zip(a, a)

def parse_directive(line: str) -> Tuple[str, str]:
    assert line.startswith("#"), "directive does not start with `#`"
    parts = iter(line[1:].split())
    directive = ""
    while directive not in ["if", "ifdef", "ifndef", "define", "undef", "include", "endif", "else", "elif", "error"]:
        # print(f"directive: {directive}")
        directive += next(parts).strip()
    argument = " ".join(parts)
    # print(f"directive: {directive}, argument: {argument}")
    return directive, argument

def strip_extra_whitespace(line: str) -> str:
    return line.strip()

def nonempty(container) -> bool:
    return len(container) != 0

def prepare(path: str | Path) -> list[str]:
    with open(path) as f:
        data = f.readlines()
    data = map(strip_extra_whitespace, data)
    data = filter(nonempty, data)
    data = list(data)
    return data