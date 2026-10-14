import sys
sys.path.insert(0,'tools/python')
from capstone import *
from pathlib import Path
b=Path(sys.argv[3] if len(sys.argv)>3 else 'work/ssf2xjr1-decrypted.bin').read_bytes()
c=Cs(CS_ARCH_M68K,CS_MODE_BIG_ENDIAN|CS_MODE_M68K_000)
s=int(sys.argv[1],16); e=int(sys.argv[2],16)
p=s
while p<e:
  ins=list(c.disasm(b[p:p+10],p,1))
  if not ins: print(f'{p:06x} {b[p:p+2].hex()} .word'); p+=2; continue
  i=ins[0]; print(f'{i.address:06x} {i.bytes.hex():20} {i.mnemonic:10} {i.op_str}'); p+=i.size
