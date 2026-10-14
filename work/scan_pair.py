import sys,re
sys.path.insert(0,'tools/python')
from capstone import *
from pathlib import Path
b=Path('work/ssf2xjr1-ryu-crmk-window.bin').read_bytes()
c=Cs(CS_ARCH_M68K,CS_MODE_BIG_ENDIAN|CS_MODE_M68K_000)
r1=re.compile(r'movea\.l \$1a\((a\d)\), (a\d)')
p=0; prev=[]
while p<0x300000:
  ins=list(c.disasm(b[p:p+10],p,1))
  if not ins: p+=2; prev=[]; continue
  i=ins[0]; s=f'{i.mnemonic} {i.op_str}'
  for (pa,reg) in prev:
    if re.search(r'\$c\('+reg+r'\)',s) and p-pa<24: print(f'{pa:06x} -> {p:06x} {s}')
  m=r1.search(s)
  prev=[(pa,r) for pa,r in prev if p-pa<24]
  if m: prev.append((p,m.group(2)))
  p+=i.size
