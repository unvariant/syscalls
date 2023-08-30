#!/usr/bin/python3

from z3 import *

_MIPS_SIM, __NR_Linux, o32, n64, n32 = Ints('sim linux o32 n64 n32')

s = Solver()
s.add(
    And(
        If(
            _MIPS_SIM == 1,
            And(__NR_Linux == 4000, o32 == 1),
                    If(
            3 == _MIPS_SIM,
            And(__NR_Linux == 5000, n64 == 1),
            True
        ),
        ),
    )
)
s.add(o32 != 1)
s.add(n64 == 1)
s.add(n32 != 1)
print(s.check())
print(s.model())