from pathlib import Path
from sys import argv
from z3 import *
import subprocess
import logging
import re

set_option(max_args=10000000, max_lines=1000000, max_depth=10000000, max_visited=1000000)
set_option('model_evaluator.completion', True)
BoolRef.__or__ = lambda self, rhs: Or(self, rhs)
BoolRef.__and__ = lambda self, rhs: And(self, rhs)
BoolRef.__invert__ = lambda self: Not(self)
logging.basicConfig(level=logging.ERROR)

predefined = subprocess.run("gcc -E -dD -P - < /dev/null", shell=True, check=True, capture_output=True, text=True).stdout.strip().split("\n")
predefined = map(lambda ln: ln.split()[1], predefined)
predefined = list(map(lambda name: name[:name.index("(")] if "(" in name else name, predefined))
nr_pattern = re.compile(r"_NR_[a-z]+")

def isbadname(name):
    global predefined
    badsuffix = any([name.endswith(suffix) for suffix in ["_H", "_H_"]])
    badpredefined = name in predefined
    return any([badsuffix, badpredefined])

def defined(var):
    return var != 0

def define(env, name, value="1"):
    if isbadname(name):
        return True
    value = fix(env, value)
    try:
        _ = IntVal(value)
        if not name in env:
            sym = Int(name)
            env[name] = sym
        return env[name] == value
    except Z3Exception:
        return True

def nonempty(lst):
    return list(filter(len, lst))

def conv(code):
    return code.replace("!", " ~ ").replace("||", " | ").replace("&&", " & ")

def fix(env, expr):
    while True:
        try:
            return eval(expr, env)
        except NameError as e:
            if not e.name in env:
                env[e.name] = Int(e.name)
                continue

def include(env, path):
    defines = subprocess.run(f"gcc -E -dD -P {path}", shell=True, check=True, capture_output=True, text=True).stdout.strip().split("\n")
    implies = []
    for ln in defines:
        if ln.startswith("#define"):
            cmd, name, *value = ln.split()
            if isbadname(name):
                continue
            value = " ".join(value).strip()
            if len(value) == 0:
                value = "1"
            try:
                implies.append(define(env, name, value))
            except (SyntaxError, NameError) as e:
                logging.warning(f"failed to parse `{ln}`")
    return implies

def compile(env, cond, implied, otherwise):
    stmt = If(fix(env, cond), And(*implied), And(*otherwise))
    return stmt

def parse(env, it, path, files, cond="True", consequences=[]):
    implied = []
    otherwise = consequences
    consequences = []

    while True:
        try:
            ln = next(it)
        except StopIteration:
            return compile(env, cond, implied, otherwise)

        if len(ln) > 1:
            name = ln[1]
        cmd = ln[0].lower()

        match cmd:
            case "#if":
                check = conv(" ".join(ln[1:]))
            case "#ifdef":
                check = f"{name} != 0"
            case "#ifndef":
                check = f"{name} == 0"
                if isbadname(name):
                    check = "True"
            case "#elif":
                check = conv(" ".join(ln[1:]))
            case "#else":
                check = f"True"
            case "#endif":
                return compile(env, cond, implied, otherwise)
            case "#define":
                if len(ln) == 2:
                    implied.append(define(env, name))
                else:
                    implied.append(define(env, name, " ".join(ln[2:])))
            case "#include":
                name = name[1:-1].strip()
                if "unistd" in name:
                    implied.append(define(env, name))
                    # otherwise.append(env[name] == 0)
                    files.append(name)
                else:
                    relative = path / name
                    logging.info(f"include: parsing #defines in `{relative}`")
                    implied += include(env, relative)

        if cmd in ["#if", "#ifdef", "#ifndef", "#elif", "#else"]:
            fix(env, check)
            switch = parse(env, it, path, files, cond=check)
            if cmd in ["#elif", "#else"]:
                return compile(env, cond, implied, [switch] + otherwise)
            else:
                implied.append(switch)

if len(argv) < 2:
    print("provide location of headers directory")
    exit(1)

headers = Path(argv[1])

for header in headers.glob("**/include/asm/unistd.h"):
    print(f"==[ {header} ]==")
    include_path = Path(*header.parts[:-2])
    lines = []
    for line in subprocess.run(f"gcc -E -dD -fpreprocessed -P {header}", shell=True, check=True, capture_output=True, text=True).stdout.split("\n"):
        if line.startswith("#"):
            parts = line.strip().split()
            parts = filter(lambda n: len(n) != 0, parts)
            parts = list(parts)
            if parts[0] == "#":
                parts = [parts[0] + parts[1]] + parts[2:]
            lines.append(parts)

    env = {"defined": defined, "__really_really_bad_consequences": Int('you-fucked-up'), }
    files = []
    constraints = parse(env, iter(lines), include_path, files)
    constraints = simplify(constraints)
    for file in files:
        s = Solver()
        s.add(constraints)
        s.add(env[file] == 1)
        for other in filter(lambda n: n != file, files):
            s.add(env[other] == 0)
        s.check()
        m = s.model()

        defines = []
        for var in m:
            if str(var) in files:
                continue
            value = m[var].as_long()
            if value == 0:
                continue
            defines.append(f"-D {var}={value}")
        defines = " ".join(defines)
        #output = subprocess.run(f"gcc -dD -E -P {defines} {include_path / file}", shell=True, check=True, capture_output=True, text=True).stdout.strip().split("\n")
        output = subprocess.run(f"zig translate-c {defines} -I {include_path} {include_path / 'asm/unistd.h'}", shell=True, check=True, capture_output=True, text=True).stdout.strip().split("\n")
        output = map(lambda s: s.strip(), output)
        output = filter(nonempty, output)
        
        arch = include_path.parent.name
        abi = Path(file).stem
        if "_" in abi:
            abi = abi[abi.index("_")+1:]
        elif "-" in abi:
            abi = abi[abi.index("-")+1:]
        else:
            abi = "generic"
        with open(headers / f"{arch}-{abi}.nr", "w+") as f:
            f.write("\n".join(output))