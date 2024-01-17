from util import *
import logging
import re
from pprint import pprint, pformat

class Scope:
    def __init__(self, constraint):
        self.vars = {}
        self.constraint = constraint

    def __repr__(self):
        return pformat([ self.constraint, self.vars ], indent=4)

class Env:
    def __init__(self, constraint):
        self.parent = None
        self.vars = {}
        self.constraint = constraint
        self.unistd = []

    def set(self, key, val):
        logging.debug(f"KEY: `{key}`, VAL: `{val}`")
        self.vars[key] = val

    def get(self, key):
        if key in self.vars:
            return self.vars[key]
        if parent != None:
            return self.parent.get(key)
        raise KeyError(key)

    def push(self, constraint):
        logging.debug(f"PUSH: {constraint}")
        new = Env(constraint)
        new.parent = self
        return new

    def pop(self):
        logging.debug(f"POP:  {self.constraint}")
        return self.parent

    def pushEnv(self, new):
        logging.debug(f"PUSH: {new.constraint}")
        new.parent = self
        return new

    def depth(self):
        if self.parent:
            return 1 + self.parent.depth()
        return 1

    def __repr__(self):
        return pformat([
            self.constraint,
            self.unistd,
            self.vars,
            self.parent
        ], indent=4)

def parse(lines, env, results, include="include", i=0, unistd=0, depth=0):
    branches = []
    save = env

    while i < len(lines):
        line = lines[i]
        i += 1

        if not line.startswith("#"):
            continue

        directive, argument = parse_directive(line)
        match directive:
            case "if":
                env = env.push(argument)

            case "ifdef":
                env = env.push(f"1 == {argument}")

            case "ifndef":
                env = env.push(f"0 == {argument}")

            case "elif":
                branches.append(env)
                env = env.pop()
                env = env.push(argument)

            case "else":
                branches.append(env)
                previous = " | ".join(f"({e.constraint})" for e in branches)
                env = env.pop()
                env = env.push(f"not ({previous})")

            case "endif":
                branches.append(env)
                env = env.pop()
                start = i

                current = str(env)

                env = env.push("True")
                parse(lines, env, results, include=include, i=start, unistd=unistd, depth=depth+1)
                env = env.pop()

                assert str(env) == current

                for scope in branches:
                    env = env.pushEnv(scope)
                    parse(lines, env, results, include=include, i=start, unistd=unistd, depth=depth+1)
                    env = env.pop()

                    assert str(env) == current
                return

            case "define":
                arguments = argument.split()
                key = arguments[0]
                val = "1"
                if len(arguments) >= 2:
                    val = " ".join(arguments[1:])
                env.set(key, val)

            case "include":
                localpath = argument.strip("<").strip(">")
                if re.search(r"unistd(?:_|-)\w+\.h", localpath):
                    logging.info(f"including {localpath}")
                    env.unistd.append(localpath)
                    logging.info(f"unistd: {env}")
                    pprint(lines[:i])
                    pprint("==============")
                    pprint(lines[i:])
                    pprint("==============")
                    pprint(lines[i])
                # else:
                #     lines = lines[:i] + prepare(include / localpath) + lines[i:]
                lines = lines[:i] + prepare(include / localpath) + lines[i:]
                logging.info(f"ENV:CONSTRAINT: {env.constraint}, INCLUDING: {localpath}")

    node = env
    unistd = []
    while node != None:
        unistd += [node.unistd]
        node = node.parent
    if len(unistd) <= 2:
        pprint("==[ SCOPE ]==" + str(unistd))
        pprint(env)
    pprint(unistd)