#!/usr/bin/env python3
"""Regression test: valid all-zero MIPS code caves must not be counted as mismatches."""
from pathlib import Path
import re
root=Path(__file__).resolve().parent
c=(root.parent/'main.c').read_text()
assert 'if(expected==0u || got!=expected)' not in c
assert 'if((guards[i].expected!=0u && expected==0u) || got!=expected)' in c
assert 'if((patches[i].expected!=0u && expected==0u) || got!=expected)' in c
guards=[tuple(int(x,16) for x in line.split()) for line in (root/'guards.txt').read_text().splitlines()]
zero=[a for a,v in guards if v==0]
assert len(zero)==4, zero

def mismatch(original, expected, actual):
    # If original nonzero and rebasing produced 0, a J address failed safety validation.
    return (original != 0 and expected == 0) or actual != expected

for addr,val in guards:
    assert not mismatch(val,val,val), hex(addr)
    assert mismatch(val,val,val^1), hex(addr)
assert mismatch(0x08001234,0,0)  # failed J address can never pass
print('PASS v4.1 zero-guard false-positive fixed; 4/23 original 0-valued guards are valid.')
print('PASS mismatched words and unsafe relocation still fail closed.')
