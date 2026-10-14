import struct, json, sys
from pathlib import Path
sys.path.insert(0, 'work')
from cps2emu import CPS2, raw_program

builds = {
    'original': (Path('work/ssf2xjr1-decrypted.bin').read_bytes(), raw_program('ssf2xjr1.zip')),
    'com_problema': (Path('work/ssf2xjr1-ryu-air-tatsu-juggle2.bin').read_bytes(), raw_program('backup/ssf2xjr1-before-timer-fix.zip')),
    'corrigida': (Path('work/ssf2xjr1-fixed.bin').read_bytes(), raw_program('work/fixed-enc.zip')),
}
HELPERS = {0x953dc: 0xb1, 0x956b0: 0x95, 0x7fd10: 0xa1, 0x80014: 0xe1, 0x7fb48: 0x99, 0x7fe72: 0x95,
           0x852ce: 0xe7, 0x85574: 0xeb, 0x856ca: 0x91, 0x8dc5c: 0x85, 0x8ddb4: 0x81}
A6, STOP = 0xff844e, 0x300000

def run(build, helper, dest, i):
    dec, raw = builds[build]
    e = CPS2(dec, raw); u = e.u
    from unicorn.m68k_const import UC_M68K_REG_A6, UC_M68K_REG_A7, UC_M68K_REG_D0, UC_M68K_REG_PC
    from unicorn import UC_HOOK_CODE
    def rnd(u, a, s, d):
        u.reg_write(UC_M68K_REG_D0, i)
        sp = u.reg_read(UC_M68K_REG_A7); u.reg_write(UC_M68K_REG_A7, sp + 4)
        u.reg_write(UC_M68K_REG_PC, int.from_bytes(u.mem_read(sp, 4), 'big'))
    u.hook_add(UC_HOOK_CODE, rnd, begin=0x2e96, end=0x2e96)
    u.reg_write(UC_M68K_REG_A6, A6); u.reg_write(UC_M68K_REG_A7, 0xff7000)
    u.mem_write(0xff7000, struct.pack('>I', STOP))
    u.emu_start(helper, STOP, count=300)
    return u.mem_read(A6 + dest, 1)[0]

res = {}
for h, dest in HELPERS.items():
    vals = {b: [run(b, h, dest, i) for i in range(32)] for b in builds}
    res[hex(h)] = {b: vals[b] for b in builds}
    assert vals['corrigida'] == vals['original'], (hex(h), vals)
    print(hex(h), 'original', vals['original'][:8], '| com problema', vals['com_problema'][:8], '| corrigida ok')
Path('work/timer-tables-cps2-tests.json').write_text(json.dumps(res))
