import struct, json, sys
from pathlib import Path
sys.path.insert(0, 'work')
from cps2emu import CPS2, raw_program
from unicorn import UC_HOOK_CODE
from unicorn.m68k_const import UC_M68K_REG_A6, UC_M68K_REG_A7, UC_M68K_REG_D0, UC_M68K_REG_PC

assert Path('work/rdc-verify.bin').read_bytes() == Path('work/ssf2xjr1-ryu-dp-claw.bin').read_bytes()
builds = {
    'original': (Path('work/ssf2xjr1-decrypted.bin').read_bytes(), raw_program('ssf2xjr1.zip')),
    'v0.1': (Path('work/ssf2xjr1-ken-dp-ryu.bin').read_bytes(), raw_program('backup/ssf2xjr1-v0.1.zip')),
    'nova': (Path('work/ssf2xjr1-ryu-dp-claw.bin').read_bytes(), raw_program('work/ryu-dp-claw-enc.zip')),
}
RYU, OPP, STOP, PTR = 0xff844e, 0xff884e, 0x300000, 0x12345678 & 0xfffffe

def run(build, st3=0x0a, move=4, strength=4, o_char=11, o_old=0, o_st3=0x0e, o_stop=10):
    dec, raw = builds[build]
    e = CPS2(dec, raw); u = e.u
    for base, vals in ((RYU, {3: st3, 0x88: move, 0x9b: strength}),):
        for off, v in vals.items(): u.mem_write(base + off, bytes([v]))
    u.mem_write(RYU + 0x39e, struct.pack('>H', OPP & 0xffff))
    for base in (OPP, 0xffff0000 | (OPP & 0xffff)):
        u.mem_write(base + 0x391, bytes([o_char])); u.mem_write(base + 0x3b6, bytes([o_old]))
        u.mem_write(base + 3, bytes([o_st3])); u.mem_write(base + 0x47, bytes([o_stop]))
        u.mem_write(base + 0x11a, struct.pack('>I', PTR))
    u.reg_write(UC_M68K_REG_A6, RYU); u.reg_write(UC_M68K_REG_A7, 0xff7000)
    u.emu_start(0x7fb7e, 0x7fb84, count=200)
    return u.mem_read(RYU + 3, 1)[0], hex(int.from_bytes(u.mem_read(0xffff0000 | (OPP & 0xffff) + 0x11a, 4), 'big'))

cases = {
    'cancel_fierce_dp_vs_claw_hitstop': (dict(), True),
    'cancel_fierce_dp_vs_claw_sliding': (dict(o_stop=0), False),
    'cancel_jab_dp_vs_claw':            (dict(strength=0), False),
    'cancel_fierce_hadouken_vs_claw':   (dict(move=0), False),
    'dp_from_neutral_vs_claw':          (dict(st3=0x00), False),
    'cancel_fierce_dp_vs_old_claw':     (dict(o_old=1), False),
    'cancel_fierce_dp_vs_ken':          (dict(o_char=4), False),
    'cancel_fierce_dp_vs_fei':          (dict(o_char=14), False),
    'cancel_fierce_dp_claw_blocking':   (dict(o_st3=0x14), False),
}
res = {}
for name, (kw, changed) in cases.items():
    o, a, n = (run(b, **kw) for b in builds)
    res[name] = {'original': o, 'v0.1': a, 'nova': n}
    assert o == a and n[0] == 0x0c == o[0], (name, o, a, n)
    assert (n[1] == '0x792d4') if changed else (n == o), (name, o, n)

def timer(build, helper, dest, i):
    dec, raw = builds[build]
    e = CPS2(dec, raw); u = e.u
    def rnd(u, a, s, d):
        u.reg_write(UC_M68K_REG_D0, i)
        sp = u.reg_read(UC_M68K_REG_A7); u.reg_write(UC_M68K_REG_A7, sp + 4)
        u.reg_write(UC_M68K_REG_PC, int.from_bytes(u.mem_read(sp, 4), 'big'))
    u.hook_add(UC_HOOK_CODE, rnd, begin=0x2e96, end=0x2e96)
    u.reg_write(UC_M68K_REG_A6, RYU); u.reg_write(UC_M68K_REG_A7, 0xff7000)
    u.mem_write(0xff7000, struct.pack('>I', STOP))
    u.emu_start(helper, STOP, count=300)
    return u.mem_read(RYU + dest, 1)[0]
orig = builds['original'][0]
for h in (0x8df18, 0x8e07c, 0x91eb8):
    dest = orig[h + 13]
    assert [timer('nova', h, dest, i) for i in range(32)] == [timer('original', h, dest, i) for i in range(32)], hex(h)
res['converted_timer_helpers_identical'] = True
Path('work/ryu-dp-claw-tests.json').write_text(json.dumps(res, indent=2))
for k, v in res.items(): print(k, v)
