#!/usr/bin/python3

from z3 import *
from pathlib import Path
import logging
import re
from util import *
import tempfile
import json
from multiprocessing import Pool
from v2 import *
import argparse
import mapping

logging.basicConfig(level=logging.INFO)

parser = argparse.ArgumentParser(
    prog="parse.py",
    description="parse kernel source for syscall definitions",
)
parser.add_argument("--tag", help="kernel tag", required=True)
parser.add_argument("--static", help="static file directory", default="static")
parser.add_argument("-j", help="number of processes", default=4, type=int)

args = parser.parse_args()
processes = args.j
version = args.tag
cache = Path("cache")
static = Path("static")
json_dir = static / version

linux = cache / version / "linux"
with open(Path(json_dir / "archlist.json"), "r") as f:
    archlist = json.load(f)
arch_specific: dict[str, dict] = {}
arch_generic: dict[str, dict] = { "normal": {}, "compat": {}, }
signatures: dict[str, list[Tuple[str, str]]] = {}


def load_signatures(signatures: dict[str, list[Tuple[str, str]]]):
    signatures_file = linux / "include" / "linux" / "syscalls.h"
    signatures_cache = json_dir / "signatures.json"
    if signatures_cache.exists():
        with open(signatures_cache, "r") as f:
            signatures.update(json.load(f))
    else:
        tags = run(f"ctags --language-force=c --fields='{{name}}{{signature}}' --kinds-c='+p' -u --output-format=json -o - {signatures_file}").stdout
        tags = tags.strip().split("\n")
        tags = filter(lambda s: len(s) > 0, tags)
        tags = map(lambda txt: json.loads(txt), tags)
        for tag in tags:
            if "signature" in tag and tag["name"].startswith("sys_"):
                syscall = tag["name"][4:]
                args = tag["signature"][1:-1].split(",")
                args = map(lambda arg: tuple(arg.rsplit(" ", 1)) if " " in arg else (arg, ""), args)
                args = list(args)
                signatures[syscall] = args

        with open(signatures_cache, "w+") as f:
            f.write(json.dumps(signatures))

def parse_syscalls(tags: str):
    syscalls = { "normal": {}, "compat": {}, }

    tags = tags.strip().split("\n")
    tags = filter(lambda s: len(s) > 0, tags)
    tags = map(lambda txt: json.loads(txt), tags)

    for tag in tags:
        if "signature" in tag:
            if tag["name"].startswith("SYSCALL_DEFINE"):
                syscall, *args = tag["signature"][1:-1].split(",")
                args = list(grouppairs(args))

                if syscall in syscalls["normal"]:
                    logging.warn(f"{syscall} already found")

                syscalls["normal"][syscall] = { "name": syscall, "args": args, "path": str(Path(tag["path"]).relative_to(linux)), "line": int(tag["line"]), }
            elif tag["name"].startswith("COMPAT_SYSCALL_DEFINE"):
                syscall, *args = tag["signature"][1:-1].split(",")
                args = list(grouppairs(args))
                syscalls["compat"][syscall] = { "name": syscall, "args": args, "path": str(Path(tag["path"]).relative_to(linux)), "line": int(tag["line"]), }
            elif tag["name"].startswith("sys_"):
                syscall = tag["name"][4:]

                if syscall in syscalls["normal"]:
                    logging.warn(f"{syscall} already found")

                if not syscall in syscalls["normal"]:
                    args = tag["signature"][1:-1].split(",")
                    args = map(lambda arg: tuple(arg.rsplit(" ", 1)) if " " in arg else (arg, ""), args)
                    args = list(args)
                    syscalls["normal"][syscall] = { "name": syscall, "args": args, "path": str(Path(tag["path"]).relative_to(linux)), "line": int(tag["line"]), }
            elif tag["name"].startswith("GLOBAL_ENTRY") or tag["name"].startswith("ENTRY"):
                syscall = tag["signature"][1:-1]
                if syscall.startswith("sys_"):
                    syscall = syscall[4:]
                logging.debug(f"name: {syscall}")
                args = signatures.get(syscall, [["?", ""]])

                if syscall in syscalls["normal"]:
                    logging.warn(f"{syscall} already found")
                    
                syscalls["normal"][syscall] = { "name": syscall, "args": args, "path": str(Path(tag["path"]).relative_to(linux)), "line": int(tag["line"]), }

    return syscalls

def arch_specific_load(arch: str):
    archdir = linux / "arch" / arch
    tags = run(f"ctags --language-force=c --fields='{{name}}{{signature}}{{input}}{{line}}' -u -R --exclude='*.h' --exclude='*generated*' --output-format=json -o - {archdir}")
    syscalls = parse_syscalls(tags.stdout)

    entries = run(rf"rg '^\s*(?:GLOBAL_)?ENTRY\((.*?)\)\s*$' -t asm -g '!*testing*' --json {archdir}").stdout
    entries = entries.strip().split("\n")
    entries = map(lambda txt: json.loads(txt), entries)

    for entry in entries:
        if entry["type"] != "match":
            continue
        
        entry = entry["data"]
        name = entry["lines"]["text"].strip()
        name = name[name.find("(")+1 : name.rfind(")")]
        if name.startswith("sys_"):
            name = name[4:]
        args = signatures.get(name, [["?", ""]])
        path = str(Path(entry["path"]["text"]).relative_to(linux))
        line = int(entry["line_number"])

        if not name in syscalls["normal"]:
            syscalls["normal"][name] = { "name": name, "args": args, "path": path, "line": line, }

    return syscalls

def arch_generic_load(path: str):
    tags = run(f"ctags --language-force=c --fields='{{name}}{{signature}}{{input}}{{line}}' -u -R --exclude='*.h' --exclude='*generated*' --exclude='*arch*' --exclude='*tools*' --output-format=json -o - {path}")
    return parse_syscalls(tags.stdout)

def load_syscalls(specific: dict, generic: dict):
    generic_cache = json_dir / "generic.json"

    if generic_cache.exists():
        with open(generic_cache, "r") as f:
            generic.update(json.load(f))
    else:
        files = linux.glob("*")
        files = filter(lambda file: file.is_dir(), files)

        with Pool(processes) as pool:
            results = pool.map(arch_generic_load, files)

        for result in results:
            generic["normal"].update(result["normal"])
            generic["compat"].update(result["compat"])

        with open(generic_cache, "w+") as f:
            f.write(json.dumps(generic))

    specific_cache = json_dir / "specific.json"

    if specific_cache.exists():
        with open(specific_cache, "r") as f:
            specific.update(json.load(f))
    else:
        with Pool(processes) as pool:
            results = pool.map(arch_specific_load, archlist)

        for arch, syscalls in zip(archlist, results):
            specific[arch] = syscalls

        with open(specific_cache, "w+") as f:
            f.write(json.dumps(specific))

def jsonify(includepath: Path, defs: str):
    unistd = includepath / "asm" / "unistd.h"

    output = run(f"zig translate-c {defs} -I {includepath} {unistd}").stdout.strip().split("\n")
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
        return json.loads(run(f"zig run {zig.name}").stdout)
    
def make_searchable(args: list[Tuple[str, str]]):
    results = []
    for fulltype, name in args:
        search = fulltype.replace("*", " ").strip()
        search = search.replace(" __user", " ").strip()
        search = search.replace("unsigned ", " ").strip()
        search = search.replace("union ", " ").strip()
        search = search.replace("enum ", " ").strip()

        fulltype = fulltype.replace("const", "")
        fulltype = fulltype.replace("__kernel_old_", "old_")
        fulltype = fulltype.replace("__old_kernel_", "old_")
        fulltype = fulltype.replace("__kernel_", "")
        fulltype = fulltype.replace("__user", "")
        fulltype = fulltype.replace("compat_", "")
        fulltype = fulltype.replace("__", "")
        
        pointers = re.compile(r"\*\s+\*")
        while re.search(pointers, fulltype):
            fulltype = pointers.sub("**", fulltype)

        fulltype = re.sub(r"\s+(\*+)\s*", r" \1", fulltype)
        fulltype = fulltype.strip()

        if not " " in fulltype:
            results.append({ "fulltype": fulltype, "search": search, "name": name })
            continue

        while True:
            if search.startswith("const "):
                search = search[6:].strip()
            elif search.endswith("const"):
                search = search[:-5].strip()
            elif "struct " in search:
                search = search[search.index("struct ")+7:]
            else:
                break

        if " " in search:
            logging.info(f"search: `{search}`")
        
        results.append({ "fulltype": fulltype, "search": search, "name": name })
    return results

class ProcessArgs:
    def __init__(self, arch: str, abi: str, defs: str):
        self.arch = arch
        self.abi = abi
        self.defs = defs
    
def process(args: ProcessArgs):
    arch = args.arch
    abi = args.abi
    defs = args.defs
    includepath = cache / version / "headers" / arch / "include"
    arch_syscalls = arch_specific[arch]
    defs = map(lambda define: f"-D {define}", defs)
    defs = " ".join(defs)

    logging.info(f"processing {arch}-{abi}")
    
    with open(json_dir / f"{arch}-{abi}.json", "w+") as output:
        parsed = jsonify(includepath, defs)
        syscalls = []
        for syscall, nr in sorted(parsed.items(), key = lambda entry: entry[1]):
            info = \
                arch_syscalls["normal"].get(syscall, None) or \
                arch_generic["normal"].get(syscall, None) or \
                arch_syscalls["compat"].get(syscall, None) or \
                arch_generic["compat"].get(syscall, None) or \
                { "args": signatures.get(syscall, [["?", ""]]), "path": "undetermined", "line": "undetermined", }

            syscalls.append({
                "nr": nr,
                "name": syscall,
                "args": make_searchable(info["args"]),
                "path": info["path"],
                "line": info["line"],
            })
        output.write(json.dumps({
            "syscalls": syscalls,
        }))
    
load_signatures(signatures)
load_syscalls(arch_specific, arch_generic)

targets = []

for arch in archlist:
    if not arch in mapping.arches:
        logging.warning(f"no rules defined for {arch}")
        continue

    unistd = cache / version / "headers" / arch / "include" / "asm" / "unistd.h"
    if not unistd.exists():
        logging.warning(f"{unistd} cannot be found")
        continue

    with open(unistd, "r") as f:
        unistd = f.read()

    rules = []
    arch_rules = mapping.rules[arch]
    if arch_rules:
        for rule in arch_rules.values():
            args = mapping.Args(arch, rule.abi, unistd)
            if rule.condition(args):
                rules.append(rule)
    else:
        rules = [mapping.Rule("generic", [])]

    if len(rules) == 1:
        rules[0].abi = "generic"

    for rule in rules:
        targets.append(ProcessArgs(arch, rule.abi, rule.defs))

with Pool(processes) as pool:
    pool.map(process, targets)

archinfo = {}
for target in targets:
    archinfo.setdefault(target.arch, []).append(target.abi)

with open(json_dir / "info.json", "w+") as info:
    for v in archinfo.values():
        v.sort()
    info.write(json.dumps(archinfo))

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