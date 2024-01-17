#!/usr/bin/python3

from z3 import *
from pprint import pprint, pformat
from pathlib import Path
import logging
import re
from util import *
import itertools
from subprocess import run
import tempfile
import json

logging.basicConfig(level=logging.INFO)

from v2 import *

cache = Path("cache")
version = "v6.5-rc6"
archlist = Path(cache / version / "linux" / "arch").glob("*/")
archlist = [path.stem for path in archlist]


def jsonify(includepath: Path, defs: str):
    # predefines = run("gcc -x c /dev/null -dM -E", shell=True, capture_output=True, encoding="ascii").stdout.strip().split("\n")
    # predefines = map(lambda define: define.split()[1], predefines)
    # predefines = map(lambda define: define[:define.find("(")] if "(" in define else define, predefines)
    # predefines = map(lambda define: f"-U {define}", predefines)
    # predefines = " ".join(predefines)

    unistd = includepath / "asm" / "unistd.h"

    output = run(f"zig translate-c {defs} -I {includepath} {unistd}", shell=True, capture_output=True, encoding="ascii").stdout.strip().split("\n")
    output = map(lambda s: s.strip(), output)
    output = filter(nonempty, output)
    
    code = "\n".join(output)
    code += """
    const std = @import("std");
    const mem = std.mem;
    const json = std.json;
    const module = @This();

    pub fn main() !void {
        const fields = @typeInfo(module).Struct.decls;
        const stdout = std.io.getStdOut();
        var write_stream = json.writeStream(stdout.writer(), .{ .whitespace = .minified });
        defer write_stream.deinit();
        try write_stream.beginObject();
        inline for (fields) |field| {
            const name = field.name;
            comptime {
                @setEvalBranchQuota(99999999);
                var ok = false;
                if (mem.indexOf(u8, name, "_NR_")) |i| {
                    if (std.ascii.isLower(name[i + 4])) {
                        ok = true;
                    }
                }
                if (!ok) continue;
            }
            try write_stream.objectField(name[mem.indexOf(u8, name, "_NR_").? + 4 ..]);
            try write_stream.write(@field(module, name));
        }
        try write_stream.endObject();
    }
    """

    with tempfile.NamedTemporaryFile(suffix=".zig") as zig:
        zig.write(code.encode())
        zig.flush()
        return json.loads(run(f"zig run {zig.name}", shell=True, capture_output=True, encoding="ascii").stdout)

arches = {}
for arch in archlist:
    unistd = Path(cache / version / "headers" / arch / "include" / "asm" / "unistd.h")
    if not unistd.exists():
        continue

    data = prepare(unistd)
    results = {}
    includepath = Path(cache / version / "headers" / arch / "include").absolute()
    p = Parser(data, includepath=includepath)

    instrs = p.parse()

    def process(instrs: list[Instr], conditions=[], defines=[]):
        for instr in instrs:
            match instr.type():
                case Instr.DEFINE:
                    defines.append(instr)

                case Instr.BRANCH:
                    for condition, body in instr.map.items():
                        cutoff = len(defines)
                        conditions.append(condition)
                        process(body, conditions=conditions, defines=defines)
                        conditions.pop()
                        defines = defines[:cutoff]

                case Instr.INCLUDE:
                    s = Solver()
                    decls = {}
                    decls["s"] = s
                    decls["defined"] = lambda x: x != 0
                    decls["flip"] = lambda x: x == False

                    for define in defines:
                        decls[define.key] = Int(define.key)
                        try:
                            eval(f"s.add({define.key} == {define.value})", {}, decls)
                        except NameError as e:
                            decls[e.name] = Int(e.name)

                    important = []
                    for cond in conditions:
                        while True:
                            try:
                                eval(cond.condition, {}, decls)
                                break
                            except NameError as e:
                                decls[e.name] = Int(e.name)
                                important.append(e.name)

                        eval(f"s.add(({cond.condition}))", {}, decls)
                    
                    s.check()
                    m = s.model()
                    defs = []
                    for name in important:
                        key = decls[name]
                        val = m[key].as_long()
                        if val:
                            defs.append(f"-D {key}={val}")
                    defs = " ".join(defs)

                    # with open(cache / version / "json" / f"{arch}-{instr.abi}.json", "w+") as output:
                    #     parsed = jsonify(includepath, defs)
                    #     syscalls = []
                    #     for syscall, nr in sorted(parsed.items(), key = lambda entry: entry[1]):
                    #         syscalls.append({
                    #             "nr": nr,
                    #             "name": syscall,
                    #             "args": [],
                    #             "path": "tbd",
                    #         })
                    #     output.write(json.dumps({
                    #         "syscalls": syscalls,
                    #     }))
                    arches.setdefault(arch, []).append(instr.abi)

    print(f"===[ {arch} ]===")
    process(instrs)

with open("static/json/info.json", "w+") as info:
    info.write(json.dumps(arches))

# def collect(instrs: list[Instr], accum: list[list[BranchId]]):
#     for instr in instrs:
#         match instr.type():
#             case Instr.BRANCH:
#                 accum += [list(instr.map.keys())]
#                 for body in instr.map.values():
#                     collect(body, accum)

# def process(instrs: list[Instr], selected: list[BranchId]):
#     accum = []
#     for instr in instrs:
#         match instr.type():
#             case Instr.BRANCH:
#                 key = next(filter(lambda key: key in selected, instr.map.keys()))
#                 accum += process(instr.map[key], selected)
#             case Instr.DEFINE:
#                 accum.append(instr)
#             case Instr.INCLUDE:
#                 accum.append(instr)
#     return accum


# branches  = []
# collect(instrs, branches)

# print(f"[+] done collecting")
# print(f"[+] len(branches): {len(branches)}")

# ps = list(itertools.product(*branches))

# print(f"[+] processing...")

# maybe = []
# for p in ps:
#     p = process(instrs, p)
#     includes = sum(map(lambda instr: instr.type() == Instr.INCLUDE, p))
#     if includes == 1 and maybe.count(p) == 0:
#         maybe.append(p)

# for m in maybe:
#     print(f"===[ POSSIBLILTY ]===")
#     pprint(m)