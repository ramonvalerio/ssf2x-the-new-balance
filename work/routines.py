import sys
sys.path.insert(0,'tools/python')
from capstone import *
from pathlib import Path
b=Path('work/ssf2xjr1-decrypted.bin').read_bytes()
c=Cs(CS_ARCH_M68K,CS_MODE_BIG_ENDIAN|CS_MODE_M68K_000)
for start,end in [(0x95180,0x95194),(0x44d0,0x44ec),(0x4542,0x4570)]:
 for i in c.disasm(b[start:end],start): print(f'{i.address:06x} {i.bytes.hex():20} {i.mnemonic:10} {i.op_str}')
