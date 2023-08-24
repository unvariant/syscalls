from pathlib import Path
import subprocess
import json
import logging
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
            "path": "??",
            "args": [],
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

    def load_syscalls(self, directory, invert=False):
        syscalls = {}
        invert = "!" if invert else ""

        # possibly merge the two searches into a single one
        # then determine which regex was matched afterwards

        for match in self.search(rf"rg -g '{invert}{directory}' --multiline --multiline-dotall --json --type c 'asmlinkage\s+\w+\s+sys_([a-z0-9]_?)+\([^(]*?\);' ."):
            text = match["lines"]["text"]
            name = text[text.index("sys_")+4:text.index("(")]
            args = text[text.index("(")+1:text.rindex(");")].split(",")
            args = map(lambda s: s.strip(), args)
            args = map(lambda arg: tuple(arg.rsplit(maxsplit=1)), args)
            args = list(args)
            syscalls[name] = {
                "path": self.default["path"],
                "args": args,
            }
        for match in self.search(rf"rg -g '{invert}{directory}' --multiline --multiline-dotall --json --type c '^SYSCALL_DEFINE.\(\w+,.*?\)' ."):
            path = match["path"]["text"]
            line = match["line_number"]
            text = match["lines"]["text"]
            name, *args = map(lambda s: s.strip(), text[len("SYSCALL_DEFINE")+2:text.rindex(")")].split(","))
            args = [(args[i], args[i + 1]) for i in range(0, len(args), 2)]
            syscalls[name] = {
                "path": f"{path}:{line}",
                "args": args,
            }

        return syscalls

    def generate(self):
        self.generic = self.load_syscalls("arch/**", invert=True)
        for arch in self.archnames:
            self.specific[arch] = self.load_syscalls(f"arch/{arch}/**")