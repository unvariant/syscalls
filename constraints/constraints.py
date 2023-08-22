from pathlib import Path
from sys import argv
from z3 import *
import subprocess

BoolRef.__or__ = lambda self, rhs: Or(self, rhs)
BoolRef.__and__ = lambda self, rhs: And(self, rhs)
BoolRef.__invert__ = lambda self: Not(self)

def defined(var):
    return var != 0

def define(env, var, value="1"):
    sym = Int(var)
    env[var] = sym
    return sym == fix(env, value)

def nonempty(lst):
    return list(filter(len, lst))

def conv(code):
    return code.replace("!", " ~ ").replace("||", " | ").replace("&&", " & ")

def fix(env, expr):
    while True:
        try:
            return eval(expr, env)
        except NameError as e:
            env[e.name] = Int(e.name)

def compile(env, cond, implied, otherwise):
    stmt = If(fix(env, cond), And(*implied), otherwise)
    return stmt

def parse(env, it, path, cond="True"):
    implied = []

    while True:
        try:
            ln = next(it)
        except StopIteration:
            return compile(env, cond, implied, True)

        match ln[0]:
            case "#if":
                check = conv(" ".join(ln[1:]))
            case "#ifdef":
                check = f"{ln[1]} != 0"
            case "#ifndef":
                check = f"{ln[1]} == 0"
            case "#elif":
                check = conv(" ".join(ln[1:]))
            case "#else":
                check = f"True"
            case "#endif":
                return compile(env, cond, implied, True)
            case "#define":
                name = ln[1]
                if len(ln) == 2:
                    implied.append(define(env, name))
                else:
                    implied.append(define(env, name, " ".join(ln[2:])))
            case "#include":
                name = ln[1]
                if "unistd" in name:
                    implied.append(define(env, name))
                else:
                    pass
                    #implied.append(*include(name))

        if ln[0] in ["#if", "#ifdef", "#ifndef", "#elif", "#else"]:
            switch = parse(env, it, path, cond=check)
            if ln[0] in ["#elif", "#else"]:
                return compile(env, cond, implied, switch)
            else:
                implied.append(switch)

if len(argv) < 2:
    print("provide location of headers directory")
    exit(1)

headers = Path(argv[1])

for header in headers.glob("**/include/asm/unistd.h"):
    print(f"\n==[ {header} ]==")
    with open(header, "r") as f:
        lines = []
        #for line in f.readlines():
        for line in subprocess.run(f"gcc -E -dD -fpreprocessed -P {header}", shell=True, check=True, capture_output=True, text=True).stdout.split("\n"):
            if line.startswith("#"):
                parts = line.strip().split()
                parts = filter(lambda n: len(n) != 0, parts)
                parts = list(parts)
                if parts[0] == "#":
                    parts = [parts[0] + parts[1]] + parts[2:]
                lines.append(parts)

        from pprint import pprint
        env = {"defined": defined}
        constraints = parse(env, iter(lines), header)
        constraints = simplify(constraints)
        pprint(constraints)
