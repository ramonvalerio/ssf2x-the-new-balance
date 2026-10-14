"""68000 emulation that behaves like CPS2 memory decryption.

CPS2 decrypts only program-space accesses: opcode fetches and PC-relative operand reads.
Every other read of ROM returns the raw (encrypted) bytes. Tests built only on the decrypted
dump miss bugs where code reads a table through an address register.
"""
import sys, zipfile
sys.path.insert(0, 'tools/python')
from capstone import Cs, CS_ARCH_M68K, CS_MODE_BIG_ENDIAN, CS_MODE_M68K_000
from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, UC_HOOK_CODE, UC_HOOK_MEM_READ
from unicorn.m68k_const import UC_CPU_M68K_M68000

PROGRAM_FILES = ['sfxj.03c', 'sfxj.04a', 'sfxj.05', 'sfxj.06a', 'sfxj.07', 'sfxj.08']
ROM_END = 0x300000
_cs = Cs(CS_ARCH_M68K, CS_MODE_BIG_ENDIAN | CS_MODE_M68K_000)

def raw_program(zip_path):
    z = zipfile.ZipFile(zip_path)
    data = b''.join(z.read(n) for n in PROGRAM_FILES)
    out = bytearray(len(data))
    out[0::2], out[1::2] = data[1::2], data[0::2]   # files store 16-bit words byte-swapped
    return bytes(out)

class CPS2:
    def __init__(self, decrypted, raw):
        self.dec, self.raw = decrypted, raw
        self.u = u = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
        u.ctl_set_cpu_model(UC_CPU_M68K_M68000)
        u.mem_map(0, 0x1000000)
        u.mem_map(0xffff0000, 0x10000)
        u.mem_write(0, bytes(decrypted[:ROM_END]))
        self._pc_rel = False
        self._restore = []
        self.raw_reads = []
        u.hook_add(UC_HOOK_CODE, self._on_code)
        u.hook_add(UC_HOOK_MEM_READ, self._on_read, begin=0, end=ROM_END - 1)

    def _on_code(self, u, address, size, data):
        while self._restore:          # raw bytes were swapped in for the previous instruction's read
            a, b = self._restore.pop()
            u.mem_write(a, b)
        ins = next(_cs.disasm(bytes(self.dec[address:address + 10]), address, 1), None)
        self._pc_rel = ins is not None and 'pc' in ins.op_str
        self._insn = address

    def _on_read(self, u, access, address, size, value, data):
        if self._pc_rel:
            return
        self.raw_reads.append((self._insn, address, size))
        self._restore.append((address, bytes(self.dec[address:address + size])))
        u.mem_write(address, bytes(self.raw[address:address + size]))
