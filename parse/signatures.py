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
        self.generic = self.load_syscalls("arch/**", invert=True)
        self.specific = {}
        for arch in self.archnames:
            self.specific[arch] = self.load_syscalls(f"arch/{arch}/**")

    def syscall(self, arch, name):
        if arch in self.specific:
            if name in self.specific[arch]:
                return self.specific[arch][name]
        return self.generic[name]

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

        for match in self.search(rf"rg -g '{invert}{directory}' --multiline --multiline-dotall --json --type c 'asmlinkage\s+\w+\s+sys_([a-z0-9]_?)+\([^(]*?\);' ."):
            text = match["lines"]["text"]
            name = text[text.index("sys_")+4:text.index("(")]
            args = text[text.index("(")+1:text.index(");")].split(",")
            args = map(lambda s: s.strip(), args)
            args = list(args)
            syscalls[name] = {
                "path": "",
                "args": args,
            }
        for match in self.search(rf"rg -g '{invert}{directory}' --multiline --multiline-dotall --json --type c '^SYSCALL_DEFINE.\(\w+,.*?\)' ."):
            path = match["path"]["text"]
            line = match["line_number"]
            name, *args = map(lambda s: s.strip(), match["lines"]["text"][len("SYSCALL_DEFINE")+2:].split(","))
            args = [f"{args[i]} {args[i + 1]}" for i in range(0, len(args), 2)]
            syscalls[name] = {
                "path": f"{path}:{line}",
                "args": args,
            }
            if "x86" in directory:
                pprint(syscalls[name])

        return syscalls