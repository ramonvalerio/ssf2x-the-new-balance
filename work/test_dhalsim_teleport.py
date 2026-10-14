import struct, json, sys
from pathlib import Path
sys.path.insert(0, 'work')
from cps2emu import CPS2, raw_program
from unicorn import UC_HOOK_CODE
from unicorn.m68k_const import UC_M68K_REG_A6, UC_M68K_REG_A7, UC_M68K_REG_D0, UC_M68K_REG_D1, UC_M68K_REG_D2, UC_M68K_REG_PC

assert Path('work/dh-verify.bin').read_bytes() == Path('work/ssf2xjr1-dhalsim.bin').read_bytes()
builds = {
    'original': (Path('work/ssf2xjr1-decrypted.bin').read_bytes(), raw_program('ssf2xjr1.zip')),
    'nova': (Path('work/ssf2xjr1-dhalsim.bin').read_bytes(), raw_program('work/dhalsim-enc.zip')),
}
P, STOP = 0xff844e, 0x300000
LP, MP, HP, LK, MK, HK = 0x10, 0x20, 0x40, 0x100, 0x200, 0x400

def check(build, entry, mask, now, before):
    e = CPS2(*builds[build]); u = e.u
    u.mem_write(P + 0x392, struct.pack('>H', now)); u.mem_write(P + 0x394, struct.pack('>H', before))
    u.reg_write(UC_M68K_REG_A6, P); u.reg_write(UC_M68K_REG_D1, mask)
    # the caller branches on Z right after the bsr: trampoline in RAM = jsr entry.l ; seq d2 ; nop
    TR = 0xff7100
    u.mem_write(TR, bytes.fromhex('4eb9') + entry.to_bytes(4, 'big') + bytes.fromhex('57c24e71'))
    u.reg_write(UC_M68K_REG_A7, 0xff7000); u.reg_write(UC_M68K_REG_D2, 0x1234)
    u.emu_start(TR, TR + 8, count=300)
    flags = {'z': (u.reg_read(UC_M68K_REG_D2) & 0xff) == 0xff}
    return flags['z'], u.reg_read(UC_M68K_REG_D1) & 0xffff

cases = [
    ('3 socos juntos',            0x70,  LP | MP | HP, 0,               True,  True),
    ('2 socos juntos (LP+MP)',    0x70,  LP | MP,      0,               False, True),
    ('2 socos juntos (MP+HP)',    0x70,  MP | HP,      0,               False, True),
    ('2 socos juntos (LP+HP)',    0x70,  LP | HP,      0,               False, True),
    ('1 soco',                    0x70,  HP,           0,               False, False),
    ('nada',                      0x70,  0,            0,               False, False),
    ('soltar 3 socos',            0x70,  0,            LP | MP | HP,    True,  True),
    ('soltar 2 socos',            0x70,  0,            MP | HP,         False, True),
    ('soltar 1 soco',             0x70,  0,            HP,              False, False),
    ('segurando 1, aperta 2',     0x70,  LP | MP | HP, LP,              False, True),
    ('segurando 2, aperta 1',     0x70,  LP | MP | HP, LP | MP,         False, False),
    ('soco+chute (mascara socos)',0x70,  HP | HK,      0,               False, False),
    ('3 chutes',                  0x700, LK | MK | HK, 0,               True,  True),
    ('2 chutes',                  0x700, MK | HK,      0,               False, True),
    ('1 chute',                   0x700, HK,           0,               False, False),
    ('soco+chute (mascara chutes)',0x700, LP | LK,     0,               False, False),
]
res = {}
for entry, who in ((0x8af1a, 'novo'), (0x9f11e, 'antigo')):
    for name, mask, now, before, exp_o, exp_n in cases:
        (zo, d1o), (zn, d1n) = check('original', entry, mask, now, before), check('nova', entry, mask, now, before)
        res[f'{who}: {name}'] = {'original': zo, 'nova': zn}
        assert (zo, zn) == (exp_o, exp_n), (who, name, zo, zn)
        assert d1n == mask, (who, name, hex(d1n))      # mask preserved for the caller

def timer(build, helper, dest, i):
    e = CPS2(*builds[build]); u = e.u
    def rnd(u, a, s, d):
        u.reg_write(UC_M68K_REG_D0, i)
        sp = u.reg_read(UC_M68K_REG_A7); u.reg_write(UC_M68K_REG_A7, sp + 4)
        u.reg_write(UC_M68K_REG_PC, int.from_bytes(u.mem_read(sp, 4), 'big'))
    u.hook_add(UC_HOOK_CODE, rnd, begin=0x2e96, end=0x2e96)
    u.reg_write(UC_M68K_REG_A6, P); u.reg_write(UC_M68K_REG_A7, 0xff7000); u.mem_write(0xff7000, struct.pack('>I', STOP))
    u.emu_start(helper, STOP, count=300)
    return u.mem_read(P + dest, 1)[0]
orig = builds['original'][0]
for h in (0x98532, 0x986ba):
    dest = orig[h + 13]
    assert [timer('nova', h, dest, i) for i in range(32)] == [timer('original', h, dest, i) for i in range(32)], hex(h)
res['converted_timer_helpers_identical'] = True
Path('work/dhalsim-teleport-tests.json').write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding='utf-8')
for k, v in res.items(): print(k, v)
