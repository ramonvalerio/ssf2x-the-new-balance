import sys,struct,json
from pathlib import Path
sys.path.insert(0,'tools/python')
from unicorn import *
from unicorn.m68k_const import *
original=Path('work/ssf2xjr1-decrypted.bin').read_bytes()
assert original[0x951d4:0x951d8]==bytes.fromhex('0c40000a')
patched=bytearray(original); patched[0x951d7]=2
Path('work/ssf2xjr1-chicken-wing.bin').write_bytes(patched)

def run(code, sequence, base=0xff844e):
 u=Uc(UC_ARCH_M68K,UC_MODE_BIG_ENDIAN)
 u.ctl_set_cpu_model(UC_CPU_M68K_M68000); u.mem_map(0,0x1000000); u.mem_write(0,bytes(code))
 u.reg_write(UC_M68K_REG_A6,base); u.reg_write(UC_M68K_REG_A5,0xff8000)
 def hook(u,address,size,data):
  if address==0x2e96: # Isolate random timing: return a valid index into original table.
   u.reg_write(UC_M68K_REG_D0,0)
   sp=u.reg_read(UC_M68K_REG_A7); ret=int.from_bytes(u.mem_read(sp,4),'big')
   u.reg_write(UC_M68K_REG_A7,sp+4); u.reg_write(UC_M68K_REG_PC,ret)
 u.hook_add(UC_HOOK_CODE,hook)
 states=[]
 for direction in sequence:
  u.mem_write(base+0x3a6,struct.pack('>H',direction))
  u.reg_write(UC_M68K_REG_A7,0xff7000); u.mem_write(0xff7000,struct.pack('>I',0x300000))
  u.emu_start(0x95168,0x300000,count=500)
  assert u.reg_read(UC_M68K_REG_PC)==0x300000
  states.append(u.mem_read(base+0xb4,1)[0])
 return states
results={}
for label,seq in [('hcf',[1,5,4,6,2]),('old',[1,5,4,6,10]),('qcf',[4,6,2]),('forward',[2])]:
 for kind,code in [('original',original),('patched',patched)]:
  results[kind+'_'+label]=run(code,seq)
assert results['original_hcf'][-1]==6
assert results['patched_hcf'][-1]==8
assert results['original_old'][-1]==8
assert results['patched_old'][-1]==6
assert results['patched_qcf'][-1]==0
assert results['patched_forward'][-1]==0
assert run(patched,[1,5,4,6,2],0xff884e)[-1]==8
print(json.dumps(results,indent=2))
Path('work/command-tests.json').write_text(json.dumps(results,indent=2))
