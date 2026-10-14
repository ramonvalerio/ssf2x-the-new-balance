import sys,re
sys.path.insert(0,'tools/python')
from capstone import *
from pathlib import Path
b=Path('work/ssf2xjr1-ryu-crmk-window.bin').read_bytes()
c=Cs(CS_ARCH_M68K,CS_MODE_BIG_ENDIAN|CS_MODE_M68K_000)
lo,hi=int(sys.argv[1],16),int(sys.argv[2],16); rx=re.compile(sys.argv[3])
p=lo
while p<hi:
  ins=list(c.disasm(b[p:p+10],p,1))
  if not ins: p+=2; continue
  i=ins[0]; s=f'{i.mnemonic} {i.op_str}'
  if rx.search(s): print(f'{p:06x} {s}')
  p+=i.size
