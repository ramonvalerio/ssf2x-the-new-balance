import sys
sys.path.insert(0,'tools/python')
from capstone import *
from pathlib import Path
b=Path('work/ssf2xjr1-decrypted.bin').read_bytes()
c=Cs(CS_ARCH_M68K,CS_MODE_BIG_ENDIAN|CS_MODE_M68K_000)
print(b[:32].hex())
for i in c.disasm(b[0x100:0x140],0x100): print(hex(i.address),i.mnemonic,i.op_str)
for p in range(0,len(b)-2,2):
 if b[p:p+2]==bytes.fromhex('00b4') and p<0x100000:
  ins=list(c.disasm(b[max(0,p-4):p+6],max(0,p-4)))
  if any('$b4(a6)' in i.op_str for i in ins): print(hex(p),'; '.join(i.mnemonic+' '+i.op_str for i in ins))
