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
P, STOP, TR = 0xff844e, 0x300000, 0xff7100
LP, MP, HP, LK, MK, HK = 0x10, 0x20, 0x40, 0x100, 0x200, 0x400
rb = lambda u, o: u.mem_read(P + o, 1)[0]

def run_frames(build, entry, mask, frames):
    """frames: held buttons per frame; each frame runs the per-frame hook (0x782a0); the teleport check runs on the last one."""
    u = CPS2(*builds[build]).u
    u.reg_write(UC_M68K_REG_A6, P)
    prev = 0
    for k, held in enumerate(frames):
        u.mem_write(P + 0x392, struct.pack('>H', held)); u.mem_write(P + 0x394, struct.pack('>H', prev)); prev = held
        u.reg_write(UC_M68K_REG_A7, 0xff7000); u.mem_write(0xff7000, struct.pack('>I', STOP))
        u.emu_start(0x782a0, 0x782a6, count=300)
    u.mem_write(TR, bytes.fromhex('4eb9') + entry.to_bytes(4, 'big') + bytes.fromhex('57c24e71'))   # jsr check ; seq d2
    u.reg_write(UC_M68K_REG_A7, 0xff7000); u.reg_write(UC_M68K_REG_D1, mask); u.reg_write(UC_M68K_REG_D2, 0x1234)
    u.emu_start(TR, TR + 8, count=300)
    return (u.reg_read(UC_M68K_REG_D2) & 0xff) == 0xff, u.reg_read(UC_M68K_REG_D1) & 0xffff

P3, K3 = LP | MP | HP, LK | MK | HK
cases = [
    # name, mask, frames (held buttons), original, nova
    ('3 socos no mesmo frame',            0x70,  [0, P3],                          True,  True),
    ('3 socos em 2 frames (LP | MP+HP)',  0x70,  [0, LP, P3],                      False, True),
    ('3 socos em 3 frames (LP|MP|HP)',    0x70,  [0, LP, LP | MP, P3],             False, True),
    ('3 socos em 4 frames (fora)',        0x70,  [0, LP, LP, LP | MP, P3],         False, False),
    ('so 2 socos',                        0x70,  [0, LP | MP],                     False, False),
    ('so 1 soco',                         0x70,  [0, HP],                          False, False),
    ('nada',                              0x70,  [0, 0],                           False, False),
    ('segurando 2 ha muito, aperta 1',    0x70,  [LP | MP, LP | MP, LP | MP, LP | MP, P3], False, False),
    ('soltar 3 juntos',                   0x70,  [P3, P3, P3, P3, 0],              True,  True),
    ('soltar 3 em 2 frames',              0x70,  [P3, P3, P3, P3, MP | HP, 0],     False, False),
    ('3 chutes no mesmo frame',           0x700, [0, K3],                          True,  True),
    ('3 chutes em 3 frames',              0x700, [0, LK, LK | MK, K3],             False, True),
    ('3 chutes em 4 frames (fora)',       0x700, [0, LK, LK, LK | MK, K3],         False, False),
    ('socos nao contam como chutes',      0x700, [0, P3],                          False, False),
    ('chutes nao contam como socos',      0x70,  [0, K3],                          False, False),
    ('2 socos + 1 chute',                 0x70,  [0, LP | MP | LK],                False, False),
]
res = {}
for entry, who in ((0x8af1a, 'novo'), (0x9f11e, 'antigo'), (0xa7fc8, 'akuma')):
    for name, mask, frames, eo, en in cases:
        (zo, _), (zn, d1n) = run_frames('original', entry, mask, frames), run_frames('nova', entry, mask, frames)
        res[f'{who}: {name}'] = {'original': zo, 'nova': zn}
        assert (zo, zn) == (eo, en), (who, name, zo, zn)
        assert d1n == mask, (who, name, hex(d1n))

# the per-frame hook still does the original work + reversal aging
u = CPS2(*builds['nova']).u
u.reg_write(UC_M68K_REG_A6, P); u.mem_write(P + 0x169, b'\x01'); u.mem_write(P + 0x3f0, b'\x03'); u.reg_write(UC_M68K_REG_D0, 0x55)
u.reg_write(UC_M68K_REG_A7, 0xff7000); u.emu_start(0x782a0, 0x782a6, count=300)
assert rb(u, 0x169) == 0 and rb(u, 0x3f0) == 2 and u.reg_read(UC_M68K_REG_D0) == 0
res['per_frame_hook_keeps_original_and_reversal'] = True

def timer(build, helper, dest, i):
    u = CPS2(*builds[build]).u
    def rnd(u, a, s, d):
        u.reg_write(UC_M68K_REG_D0, i)
        sp = u.reg_read(UC_M68K_REG_A7); u.reg_write(UC_M68K_REG_A7, sp + 4)
        u.reg_write(UC_M68K_REG_PC, int.from_bytes(u.mem_read(sp, 4), 'big'))
    u.hook_add(UC_HOOK_CODE, rnd, begin=0x2e96, end=0x2e96)
    u.reg_write(UC_M68K_REG_A6, P); u.reg_write(UC_M68K_REG_A7, 0xff7000); u.mem_write(0xff7000, struct.pack('>I', STOP))
    u.emu_start(helper, STOP, count=300)
    return rb(u, dest)
orig = builds['original'][0]
for h in (0x98532, 0x986ba, 0x98818):
    dest = orig[h + 13]
    assert [timer('nova', h, dest, i) for i in range(32)] == [timer('original', h, dest, i) for i in range(32)], hex(h)
res['converted_timer_helpers_identical'] = True
Path('work/dhalsim-teleport-tests.json').write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding='utf-8')
for k, v in res.items(): print(k, v)
