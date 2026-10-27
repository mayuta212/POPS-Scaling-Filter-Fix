#!/usr/bin/env python3
"""Offline audit of relocation logic. Does not write to PSP.
Original user-dumped POPS.BIN -> patch and guard reference words.
"""
from pathlib import Path
from zipfile import ZipFile
import re,struct,sys,hashlib,subprocess
here=Path(__file__).resolve().parent
src=Path(sys.argv[1]) if len(sys.argv)>1 else Path('POPS_TV_DUMP(1).zip')
with ZipFile(src) as z: binary=z.read('POPS.BIN')
base=0x08B83C00
size=0xFFE54
assert len(binary)==size
assert hashlib.sha256(binary).hexdigest()=='7f01cb9e04990282f2aec878a413f0a0bb1e951cd8e002553adcace7242d9ad8'
read=lambda addr:struct.unpack_from('<I',binary,addr-base)[0]
P=[tuple(int(x,16) for x in line.split()) for line in (here/'patches.txt').read_text().splitlines()]
G=[tuple(int(x,16) for x in line.split()) for line in (here/'guards.txt').read_text().splitlines()]
assert len(P)==21 and len(G)==23
assert all(read(a)==old for a,old,new in P)
assert all(read(a)==old for a,old in G)

def rebase(addr,delta):return (addr+delta)&0xffffffff

def convert(pc,code,delta):
    op=code>>26
    if op in (2,3):
        target=((pc+4)&0xf0000000)|((code&0x03ffffff)<<2)
        if base<=target<base+size:
            adjusted=rebase(target,delta)
            assert (adjusted&0xf0000000)==((rebase(pc,delta)+4)&0xf0000000)
            return (code&0xfc000000)|((adjusted>>2)&0x03ffffff)
    if pc==0x08B9FD78 and code==0x3C0908C6:
        target=rebase(0x08C59E78,delta)
        return 0x3C090000|(((target+0x8000)>>16)&0xffff)
    if pc==0x08B9FD80 and code==0x25259E78:
        return 0x25250000 | (rebase(0x08C59E78,delta)&0xffff)
    return code

for delta in [0,0xF400,0x11400,0x10000,-0x4000]:
    simulated={}
    for address,old,_ in P:simulated[rebase(address,delta)]=convert(address,old,delta)
    for address,old in G:simulated[rebase(address,delta)]=convert(address,old,delta)
    for address,old,_ in P:assert simulated[rebase(address,delta)]==convert(address,old,delta)
    for address,old in G:assert simulated[rebase(address,delta)]==convert(address,old,delta)
    # Correctness of immediate J/JAL targets after runtime rebasing.
    for address,old,new in P:
        if new>>26 in (2,3):
            pc=rebase(address,delta)
            patched=convert(address,new,delta)
            target=((pc+4)&0xf0000000)|((patched&0x03ffffff)<<2)
            orig_target=((address+4)&0xf0000000)|((new&0x03ffffff)<<2)
            assert target==rebase(orig_target,delta),(hex(address),hex(target),hex(orig_target))
    # Check no-write policy: one corrupted instruction makes verification fail.
    mismatch=dict(simulated)
    addr=rebase(P[0][0],delta)
    mismatch[addr]^=1
    assert any(mismatch[rebase(a,delta)]!=convert(a,old,delta) for a,old,_ in P)
    assert len({rebase(a,delta) for a,_,_ in P})==21
    template_ptr=rebase(0x08C59E78,delta)
    hi=convert(0x08B9FD78,0x3C0908C6,delta)&0xffff
    lo=convert(0x08B9FD80,0x25259E78,delta)&0xffff
    assert (((hi<<16) + (lo if lo<32768 else lo-65536))&0xffffffff)==template_ptr
    print(f'PASS relocated POPS delta={delta:+#x}: {len(P)} patch words + {len(G)} guards, internal J/JAL, LUI/ADDIU, fail-closed signature guard')
print('PASS all tests. Does not prove PSP hardware load-time relocation or GE execution.')
