from pathlib import Path
import subprocess
import json
import logging
import re
from pprint import pprint

def run(cmd, cwd="."):
    logging.info(f"running `{cmd}`")
    return subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True).stdout

class Signatures:
    def __init__(self, cache: str | Path):
        self.cache = Path(cache).absolute()
        self.linux = self.cache.joinpath("linux")
        self.archnames = self.load_archnames()
        self.generic = {}
        self.specific = {}
        self.default = {
            "path": "?",
            "args": [["?", ""]] * 6,
        }

    def syscall(self, arch, name):
        logging.debug(f"arch={arch}, name={name}")
        if arch in self.specific:
            if name in self.specific[arch]:
                return self.specific[arch][name]
        if name in self.generic:
            return self.generic[name]
        return self.default

    def search(self, cmd):
        defines = run(cmd, cwd=self.linux) \
            .strip() \
            .split("\n")
        defines = map(lambda ln: json.loads(ln), defines)
        defines = filter(lambda ln: ln["type"] == "match", defines)
        defines = map(lambda ln: ln["data"], defines)
        return defines

    def load_archnames(self):
        archnames = self.linux.glob("arch/*")
        archnames = filter(lambda f: f.is_dir(), archnames)
        archnames = map(lambda f: f.stem, archnames)
        return list(archnames)

    def load_syscalls(self, cmd, parse, drop_path=False):
        syscalls = {}

        def clean(argtype):
            def REplace(victim, pattern, new):
                while m := pattern.search(victim):
                    victim = victim.replace(m.group(1), new, 1)
                return victim

            user_pointer = re.compile(r"(\s+__user)")
            extra_whitespace = re.compile(r"(\s{2,})")

            argtype = REplace(argtype, user_pointer, " ")
            argtype = REplace(argtype, extra_whitespace, " ")
            return argtype

        for match in self.search(cmd):
            prev = 0
            line = match["line_number"]
            path = match["path"]["text"]
            text = match["lines"]["text"]
            for submatch in match["submatches"]:
                start = submatch["start"]
                line += text[prev : start].count("\n")
                prev = start

                name, args = parse(submatch["match"]["text"])

                syscalls[name] = {
                    "path": self.default["path"] if drop_path else f"{path}:{line}",
                    "args": list(map(lambda arg: (clean(arg[0]), arg[1]), args))
                }

        return syscalls

    def generate(self):
        def parse_asmlinkage(match):
            name = match[match.index("sys_")+4 : match.index("(")]
            args = match[match.index("(")+1    : match.index(")")].split(",")
            args = map(lambda s: s.strip(), args)
            args = map(lambda arg: list(arg.rsplit(maxsplit=1)), args)
            args = filter(lambda arg: len(arg) == 2, args)
            args = map(tuple, args)
            args = list(args)
            return name, args

        def parse_syscall_defines(match):
            closing = match.index(")")
            if match[closing+1] == ";":
                text = match[len("SYSCALL_DEFINE")+2 : match.index(")")].split(",")
                name, *args = map(lambda s: s.strip(), text)
                args = [(args[i], args[i+1]) for i in range(0, len(args), 2)]
                return name, args
            return "", ""

        self.generic.update(
            self.load_syscalls(
                r"rg -g '!arch/**' --multiline --multiline-dotall --json --type c '^asmlinkage\s+\w+\s+sys_([a-z0-9]_?)+\(.*?\)' .",
                parse_asmlinkage
            )
        )
        self.generic.update(
            self.load_syscalls(
                r"rg -g '!arch/**' --multiline --multiline-dotall --json --type c '^SYSCALL_DEFINE.\(\w+,.*?\);' .",
                parse_syscall_defines
            )
        )
        for arch in self.archnames:
            self.specific[arch] = {}
            self.specific[arch].update(
                self.load_syscalls(
                    rf"rg -g 'arch/{arch}/**' --multiline --multiline-dotall --json --type c '^asmlinkage\s+\w+\s+sys_([a-z0-9]_?)+\(.*?\)' .",
                    parse_asmlinkage
                )
            )
            self.specific[arch].update(
                self.load_syscalls(
                    rf"rg -g 'arch/{arch}/**' --multiline --multiline-dotall --json --type c '^SYSCALL_DEFINE.\(\w+,.*?\);' .",
                    parse_syscall_defines
                )
            )

    def save(self):
        with open(self.cache / "generic.json", "w+") as f:
            json.dump(self.generic, f)
        with open(self.cache / "specific.json", "w+") as f:
            json.dump(self.specific, f)