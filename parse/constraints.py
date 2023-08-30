from pathlib import Path
from z3 import *
import subprocess
import logging
import json

def defined(var):
    return var != 0

def nonempty(lst):
    return list(filter(len, lst))

def conv(code):
    return code.replace("!", " ~ ").replace("||", " | ").replace("&&", " & ")

def run(cmd):
    return subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True).stdout

class Constraints:
    def __init__(self, cache, json_dir, signatures):
        BoolRef.__or__ = lambda self, rhs: Or(self, rhs)
        BoolRef.__and__ = lambda self, rhs: And(self, rhs)
        BoolRef.__invert__ = lambda self: Not(self)

        self.predefined = run("gcc -E -dD -P - < /dev/null").strip().split("\n")
        self.predefined = map(lambda ln: ln.split()[1], self.predefined)
        self.predefined = list(map(lambda name: name[:name.index("(")] if "(" in name else name, self.predefined))

        self.signatures = signatures
        self.cache = Path(cache).absolute()
        self.linux = self.cache / "linux"
        self.headers = self.cache / "headers"
        self.json = json_dir
        self.zig = self.cache / "zig"

        self.json.mkdir(exist_ok=True)
        self.zig.mkdir(exist_ok=True)

    def isbadname(self, name):
        badsuffix = any([name.endswith(suffix) for suffix in ["_H", "_H_"]])
        badpredefined = name in self.predefined
        return any([badsuffix, badpredefined])

    def create(self, env, name):
        if name not in env:
            env[name] = Int(name)
        return env[name]

    def constrain(self, env, name, value):
        if self.isbadname(name):
            return True
        value = self.fix(env, value)
        try:
            _ = IntVal(value)
            return self.create(env, name) == value
        except Z3Exception:
            return True

    def constant(self, env, name, value="1"):
        if self.isbadname(name):
            return True
        value = self.fix(env, value)
        try:
            _ = IntVal(value)
            env[name] = IntVal(value)
        except Z3Exception:
            pass
        return True

    def fix(self, env, expr):
        while True:
            try:
                return eval(expr, env)
            except NameError as e:
                self.create(env, e.name)

    def include(self, env, path):
        defines = run(f"gcc -E -dD -P {path}").strip().split("\n")
        implies = []
        for ln in defines:
            if ln.startswith("#define"):
                cmd, name, *value = ln.split()
                if self.isbadname(name):
                    continue
                value = " ".join(value).strip()
                if len(value) == 0:
                    value = "1"
                try:
                    implies.append(self.constant(env, name, value))
                except (SyntaxError, NameError):
                    logging.warning(f"failed to parse `{ln}`")
        return implies

    def compile(self, env, cond, implied, otherwise):
        return If(self.fix(env, cond), And(*implied), And(*otherwise))

    def parse(self, env, it, path, files, cond="True"):
        implied = []
        otherwise = [True]

        while True:
            try:
                ln = next(it)
            except StopIteration:
                return self.compile(env, cond, implied, otherwise)

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
                    if self.isbadname(name):
                        check = "True"
                case "#elif":
                    check = conv(" ".join(ln[1:]))
                case "#else":
                    check = "True"
                case "#endif":
                    return self.compile(env, cond, implied, otherwise)
                case "#define":
                    if len(ln) == 2:
                        implied.append(self.constrain(env, name, "1"))
                    else:
                        implied.append(self.constrain(env, name, " ".join(ln[2:])))
                case "#include":
                    name = name[1:-1].strip()
                    if "unistd" in name:
                        implied.append(self.constrain(env, name, "1"))
                        files.append(name)
                    else:
                        relative = path / name
                        logging.info(f"include: parsing #defines in `{relative}`")
                        implied += self.include(env, relative)

            if cmd in ["#if", "#ifdef", "#ifndef", "#elif", "#else"]:
                self.fix(env, check)
                switch = self.parse(env, it, path, files, cond=check)
                if cmd in ["#elif", "#else"]:
                    return self.compile(env, cond, implied, [switch])
                else:
                    implied.append(switch)

    def _generate_syscalls(self, identifier, unistd, include, defines):
        output = run(f"zig translate-c {defines} -I {include} {unistd}").strip().split("\n")
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
                    @setEvalBranchQuota(10000000);
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

        zig = self.zig / f"{identifier}.zig"
        with open(zig, "w+") as f:
            f.write(code)
        return json.loads(run(f"zig run {zig}"))

    def generate(self):
        archinfo = {}

        for arch in self.headers.glob("*"):
            include = self.cache / "headers" / arch / "include"
            unistd = include / "asm" / "unistd.h"
            archname = arch.stem
            abilist = []

            if not unistd.exists():
                continue

            logging.info(f"processing {unistd}")

            lines = []
            for line in run(f"gcc -E -dD -fpreprocessed -P {unistd}").split("\n"):
                if line.startswith("#"):
                    parts = line.strip().split()
                    parts = filter(lambda n: len(n) != 0, parts)
                    parts = list(parts)
                    if parts[0] == "#":
                        parts = [parts[0] + parts[1]] + parts[2:]
                    lines.append(parts)

            env = {"defined": defined, }
            files = []
            constraints = self.parse(env, iter(lines), include, files)
            constraints = simplify(constraints)

            # if nothing gets included, simply parse unistd.h itself
            if len(files) == 0:
                files = ["asm/unistd.h"]
            # solve constraints for each unistd-XXX.h abi file
            for file in files:
                s = Solver()
                s.add(constraints)
                s.add(env[file] == 1)
                for other in filter(lambda n: n != file, files):
                    s.add(env[other] != 1)
                s.check()
                m = s.model()
                print(m)

                defines = []
                for var in m:
                    value = m[var].as_long()
                    if value == 0 or str(var) in files:
                        continue
                    defines.append(f"-D {var}={value}")
                defines = " ".join(defines)

                abi = Path(file).stem
                if "_" in abi:
                    abi = abi[abi.index("_")+1:]
                elif "-" in abi:
                    abi = abi[abi.index("-")+1:]
                else:
                    abi = "generic"

                identifier = f"{archname}-{abi}"
                abilist.append(abi)

                nr = self._generate_syscalls(identifier, unistd, include, defines)
                syscalls = []
                for name, nr in nr.items():
                    info = self.signatures.syscall(archname, name)
                    syscalls.append({
                        "nr": nr,
                        "name": name,
                        "args": info["args"],
                        "path": info["path"],
                    })
                with open(self.json / f"{identifier}.json", "w+") as f:
                    json.dump({
                        "syscalls": syscalls,
                    }, f)

            archinfo[archname] = abilist

        return archinfo