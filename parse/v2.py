from util import *
import re
import logging
from pprint import pprint, pformat
from pathlib import Path


class Lines:
    def __init__(self, lines: list[str]):
        self.lines: list[str] = lines
        self.offset: int = 0

    def insert(self, lines: list[str]):
        self.lines = self.lines[:self.offset] + lines + self.lines[self.offset:]

    def peek(self) -> str:
        while self.offset < len(self.lines):
            line = self.clean(self.lines[self.offset])
            if line.startswith("#"):
                return line
            self.offset += 1
            
        return None

    def next(self) -> str:
        line = self.peek()
        self.offset += 1
        return line

    def clean(self, line: str) -> str:
        return line.strip()


class Instr:
    NONE = 0
    DEFINE = 1
    BRANCH = 2
    INCLUDE = 3

    def __init__(self): pass


class Define(Instr):
    def __init__(self, key: str, value: str):
        self.key = key
        self.value = value

    def type(self):
        return Instr.DEFINE

    def to_json(self):
        return self.__repr__()

    def __repr__(self):
        return f"{self.key} -> {self.value}"


class Branch(Instr):
    def __init__(self, map: dict[str, list[Instr]]):
        self.map = map

    def type(self):
        return Instr.BRANCH

    def __repr__(self):
        return pformat(self.map, width=1, indent=4)
    

class BranchId:
    def __init__(self, id: int, condition: str):
        self.id = id
        self.condition = condition

    def __repr__(self):
        return f"{{ id -> {self.id} - condition -> {self.condition} }}"
    

class Include(Instr):
    def __init__(self, path: Path, abi: str):
        self.path = path
        self.abi = abi

    def type(self):
        return Instr.INCLUDE
    
    def __repr__(self):
        return f"include [{self.path}]"


class Parser:
    def __init__(self, lines: list[str], includepath=Path("./include")):
        self.lines: Lines = Lines(lines)
        self.includepath: Path = includepath
        self.branch_id = 0

    def generate_branch_id(self, condition: str):
        id = self.branch_id
        self.branch_id += 1
        return BranchId(id, condition)

    def branch(self, instrs: list[Instr]):
        branches = {}
        first = None
        while line := self.lines.next():
            directive, argument = parse_directive(line)
            match directive:
                case "endif":
                    break
                case "ifdef":
                    argument = f"defined({argument})"
                    first = argument
                case "ifndef":
                    argument = f"flip(defined({argument}))"
                    first = argument
                case "if":
                    first = argument
                case "else":
                    argument = " & ".join([f"({bid.condition})" for bid in branches.keys()])
                    argument = f"flip({argument})"
            argument = argument.replace("||", " | ")
            argument = argument.replace("&&", " & ")
            branches[self.generate_branch_id(argument)] = self.parse()
        if len(branches.keys()) == 1:
            if first and first.count("_H"):
                # key = list(branches.keys())[0]
                # key.condition = "true"
                instrs += list(branches.values())[0]
                return
            else:
                branches[self.generate_branch_id("true")] = []
        instrs.append(Branch(branches))

    def parse(self):
        instrs: list[Instr] = []

        while line := self.lines.peek():
            directive, argument = parse_directive(line)
            match directive:
                case "ifdef":
                    self.branch(instrs)

                case "ifndef":
                    self.branch(instrs)

                case "if":
                    self.branch(instrs)

                case "endif" | "elif" | "else":
                    return instrs

                case "define":
                    arguments = argument.split()
                    key = arguments[0]
                    value = " ".join(arguments[1:]) if len(arguments) >= 2 else "1"
                    if "/*" in value:
                        value = value[:value.find("/*")]
                    if "//" in value:
                        value = value[:value.find("//")]
                    if not key.count("_H"):
                        instrs.append(Define(key, value))
                    self.lines.next()

                case "undef" | "error":
                    self.lines.next()

                case "include":
                    self.lines.next()
                    relative = argument.lstrip("<").rstrip(">")
                    if m := re.search(r"unistd(?:_|-)?(\w*)\.h", relative):
                        instrs.append(Include(self.includepath / relative, abi=m.group(1) or "generic"))
                    else:
                        # print(f"{relative} is not unistd")
                        self.lines.insert(prepare(self.includepath / relative))
                        
                case _:
                    print(f"unknown directive: {directive}")
                    exit(0)

        return instrs
