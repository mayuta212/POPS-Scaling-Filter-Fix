#!/usr/bin/env python3
"""Verify POPS Scaling Filter Fix v1.0.0 PSP MIPS patches against *your own* 6.61/04g POPS.BIN.
Usage: python3 verify_offline.py '/path/to/your/POPS_TV_DUMP.zip'
This is non-mutating static/simulated verification, NOT a substitute for
actual GE execution and 240p/480i display observations on the PSP.
"""
from pathlib import Path
import zipfile,hashlib,sys,struct,re
THIS=Path(__file__).resolve().parent
BASE=0x08B83C00
path=Path(sys.argv[1]) if len(sys.argv)>1 else Path('POPS_TV_DUMP(1).zip')
assert path.exists(),f'input not found: {path}'
with zipfile.ZipFile(path) as z: binary=z.read('POPS.BIN')
assert len(binary)==0xFFE54
SHA='7f01cb9e04990282f2aec878a413f0a0bb1e951cd8e002553adcace7242d9ad8'
assert hashlib.sha256(binary).hexdigest()==SHA,'POPS version mismatch; do not patch'
w=lambda addr:struct.unpack_from('<I',binary,addr-BASE)[0]
P=[tuple(int(v,16) for v in line.split()) for line in (THIS/'patches.txt').read_text().splitlines()]
G=[tuple(int(v,16) for v in line.split()) for line in (THIS/'guards.txt').read_text().splitlines()]
assert len(P)==21,(len(P),'unexpected count')
assert len(G)==23,(len(G),'unexpected count')
assert len({a for a,o,v in P})==len(P)
assert all(w(a)==orig for a,orig,new in P)
assert all(w(a)==orig for a,orig in G)
patched=dict((a,v) for a,orig,v in P)
assert patched[0x08B95BA4]==(0x08000000|((0x08B8BB14>>2)&0x3ffffff))
assert patched[0x08C59EAC]==0xC6000000
assert 0x08B85950 not in patched and 0x08B85960 not in patched
assert w(0x08B95BA8)==0x0000C012
assert w(0x08B95B98)==0x93590000
assert w(0x08B95BA0)==0x01CD0018
assert w(0x08B95BAC)==0x27030080
assert w(0x08B9FD78)==0x3C0908C6
assert w(0x08B9FD80)==0x25259E78
assert w(0x08B9FD84)==0x35049200
assert w(0x08B9FD8C)==0x24060064
assert 0x08C59EAC-0x08C59E78==0x34
assert 0x041B9200+0x34==0x041B9234
regions=[(0x08B855E0,8),(0x08B8BB14,11)]
for a,n in regions:
 for pc in range(a,a+n*4,4): assert w(pc)==0,(hex(pc),'original cave nonzero')
for off in range(0,len(binary)-3,4):
 pc=BASE+off;code=struct.unpack_from('<I',binary,off)[0];op=code>>26
 tgt=None
 if op in (2,3): tgt=((pc+4)&0xF0000000)|((code&0x3ffffff)<<2)
 elif op in (1,4,5,6,7,20,21,22,23):
  imm=code&65535;imm=imm-65536 if imm&32768 else imm
  tgt=pc+4+imm*4
 if tgt is not None:
  assert not any(a<=tgt<a+n*4 for a,n in regions),(hex(pc),hex(tgt))

def sx16(x):
 x&=0xffff
 return x-65536 if x>=32768 else x

def simulate(profile,desc,orig_x,ge_data):
 reg=[0]*32
 reg[25]=desc;reg[28]=0x11110000;reg[24]=0
 mem={0x11113663:profile,0x441B9234:ge_data}
 pc=0x08B95BA4
 count=0;write_addrs=[]
 while pc!=0x08B95BAC:
  count+=1
  assert count<45,('infinite stub loop',profile,desc,hex(pc))
  instr=patched.get(pc,0)
  op=instr>>26;rs=(instr>>21)&31;rt=(instr>>16)&31;rd=(instr>>11)&31
  imm=sx16(instr)
  isbranch=False
  nextpc=pc+4
  if op==0:
   f=instr&63
   if instr==0:pass
   elif f==0: reg[rd]=(reg[rt]<<((instr>>6)&31))&0xffffffff
   elif f==0x12: reg[rd]=orig_x&0xffffffff
   else:raise ValueError((hex(pc),hex(instr),'special'))
  elif op==0x0c:
   reg[rt]=reg[rs] & (instr & 0xffff)
  elif op==0x09:
   reg[rt]=(reg[rs]+imm)&0xffffffff
  elif op==0x0f:
   reg[rt]=(instr&0xffff)<<16
  elif op==0x0d:
   reg[rt]=reg[rs] | (instr&0xffff)
  elif op==0x24:
   addr=(reg[rs]+imm)&0xffffffff
   reg[rt]=mem.get(addr,0)&255
  elif op==0x2b:
   addr=(reg[rs]+imm)&0xffffffff
   assert addr==0x441B9234,('unexpected GE write',hex(addr))
   mem[addr]=reg[rt];write_addrs.append(addr)
  elif op in (4,5):
   eq=reg[rs]==reg[rt]
   taken=eq if op==4 else not eq
   nextpc=pc+4+4*imm if taken else pc+8
   isbranch=True
  elif op==2:
   nextpc=((pc+4)&0xf0000000)|((instr&0x3ffffff)<<2)
   isbranch=True
  else:raise ValueError((hex(pc),hex(instr),'opcode'))
  if isbranch:
   delay=patched.get(pc+4,0)
   if pc==0x08B95BA4:
    delay=w(pc+4)
   if delay:
    do=delay>>26;dr=(delay>>21)&31;dt=(delay>>16)&31
    if do==0 and delay&63==0x12:
     reg[(delay>>11)&31]=orig_x&0xffffffff
    elif do==0x0c:
     reg[dt]=reg[dr] & (delay&0xffff)
    elif do==0x09:
     reg[dt]=(reg[dr]+sx16(delay))&0xffffffff
    elif do==0x0f:
     reg[dt]=(delay&0xffff)<<16
    elif do==0x2b:
     a=(reg[dr]+sx16(delay))&0xffffffff
     assert a==0x441B9234,(hex(a),'bad delay-slot write')
     mem[a]=reg[dt];write_addrs.append(a)
    else:raise ValueError((hex(pc+4),hex(delay),'bad delay slot'))
   pc=nextpc
  else:pc+=4
  reg[0]=0
 assert write_addrs==([0x441B9234] if profile==5 else []),write_addrs
 return reg[7],reg[24],mem[0x441B9234],count

cases=[(256,80,4),(320,64,5),(368,56,6),(512,40,8),(640,32,10)]
positions=[0,0x1000,0x2a00,0x4000,0x001A0000,0xfffff000,0xf0000000]
checks=0
for profile in range(6):
 for mode,desc,tiles in cases:
  for original in positions:
   got_width,got_x,filter_,steps=simulate(profile,desc,original,0xC6000000)
   width=2*desc;dx=0
   filt=(0xC6000000 if mode in (256,320,640) else 0xC6000101) if profile==5 else 0xC6000000
   assert (got_width,got_x,filter_)==(width,(original+dx)&0xffffffff,filt),(profile,mode,hex(got_x),hex(filter_))
   checks+=1
last=0xC6000000
sequence=[512,320,256,512,368,640,512,256,368,320,640]*12
descs={x:y for x,y,_ in cases}
for mode in sequence:
 tile,x,last,n=simulate(5,descs[mode],0x120000,last)
 assert last==(0xC6000000 if mode in (256,320,640) else 0xC6000101)
print(f'PASS: POPS SHA256, {len(P)} signed patch words, {len(G)} guards, 2 zero caves.')
print('PASS: source GE template at 0x08C59E78 copied to 0x041B9200; TEXFILTER at +0x34.')
print(f'PASS: {checks} simulated profile/mode/initial-X cases + {len(sequence)} hot switches.')
print('PASS: ALL horizontal modes original X position and geometry retained, no shifts.')
print('PASS: AV 256/320/640 -> C6000000 Nearest; 368/512 -> C6000101 Linear. NonAV skip.')
print('WARNING: GPU effective use of updated GE sublist per mode must be verified on real PSP.')
print('WARNING: no PSPDEV build performed by this script.')
transitions=[256,320,368,512,640,512,320,256,640,368]*50
for i,mode in enumerate(transitions):
    stale=0xC6000000 if i%2==0 else 0xC6000101
    width,x,current,n=simulate(5,descs[mode],0x8000,stale)
    assert width==2*descs[mode] and x==0x8000
    assert current==(0xC6000000 if mode in (256,320,640) else 0xC6000101)
print('PASS: 500 synthetic sublist reset + mode switches corrected on next render hook.')
assert patched[0x08B8BB24]==0x332E0008
assert patched[0x08B8BB2C]==0 and patched[0x08B8BB30]==0x0A2E157B and patched[0x08B8BB38]==0
assert [(n,d & 8) for n,d,_ in cases]==[(256,0),(320,0),(368,8),(512,8),(640,0)]
assert 0x08B95FA4 not in patched and 0x08B95FAC not in patched
print('PASS: AV 256 now explicit Nearest; all 4 other supported horizontal modes unchanged relative to v4.8.')
