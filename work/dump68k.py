import sys
from pathlib import Path
sys.path.insert(0,'tools/python')
from capstone import *
b=Path('work/ssf2xjr1-chicken-wing.bin').read_bytes()
c=Cs(CS_ARCH_M68K,CS_MODE_BIG_ENDIAN|CS_MODE_M68K_000); c.skipdata=True
start=int(sys.argv[1],16); end=int(sys.argv[2],16)
text='\n'.join(f'{i.address:06x} {i.bytes.hex():22} {i.mnemonic:10} {i.op_str}' for i in c.disasm(b[start:end],start))
if len(sys.argv)>3: Path(sys.argv[3]).write_text(text)
else: print(text)
