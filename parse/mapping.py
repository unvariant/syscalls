from packaging import version as Version
import re

arches = [
    "alpha",
    "arc",
    "arm",
    "arm64",
    "avr32",
    "blackfin",
    "c6x",
    "csky",
    "cris",
    "frv",
    "h8300",
    "hexagon",
    "ia64",
    "loongarch",
    "m32r",
    "m68k",
    "m68knommu",
    "metag",
    "microblaze",
    "mips",
    "mn10300",
    "nds32",
    "nios2",
    "openrisc",
    "parisc",
    "powerpc",
    "s390",
    "score",
    "sparc",
    "sh",
    "tile",
    "unicore32",
    "x86",
    "xtensa",
]
narches = len(arches)

class Args:
    def __init__(self, arch: str, abi: str, unistd: str):
        self.arch = arch
        self.abi = arch
        self.unistd = unistd

class Rule:
    def __init__(self, abi: str, defs: list[str], condition=lambda args: True):
        self.abi = abi
        self.defs = defs
        self.condition = condition

def rule(arch: str, abi: str, defs=[], condition=lambda args: True):
    rules[arch][abi] = Rule(abi, defs, condition)

def has(needle: str):
    def search(args: Args):
        return needle in args.unistd
    return search

rules = dict(zip(arches, [{} for i in range(len(arches))]))

rule("arm", "oabi")
rule("arm", "eabi", ["__ARM_EABI__"], has("__ARM_EABI__"))

rule("mips", "o32", ["_MIPS_SIM=_MIPS_SIM_ABI32"])
rule("mips", "n64", ["_MIPS_SIM=_MIPS_SIM_ABI64"])
rule("mips", "n32", ["_MIPS_SIM=_MIPS_SIM_NABI32"])

rule("parisc", "32")
rule("parisc", "64", ["__LP64__"], has("__LP64__"))

rule("powerpc", "32")
rule("powerpc", "64", ["__powerpc64__"], has("__powerpc64__"))

rule("s390", "32")
rule("s390", "64", ["__s390x__"], has("__s390x__"))

rule("sh", "32")
rule("sh", "64", ["__SH5__"], has("__SH5__"))

rule("sparc", "32")
rule("sparc", "64", ["__arch64__"], has("__arch64__"))

rule("x86", "32", ["__i386__"])
rule("x86", "x32", ["__ILP32__"], has("__ILP32__"))
rule("x86", "64", [])