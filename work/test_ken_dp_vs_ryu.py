import struct, json, sys
from pathlib import Path
sys.path.insert(0, 'work')
from cps2emu import CPS2, raw_program
from unicorn import UC_HOOK_CODE
from unicorn.m68k_const import UC_M68K_REG_A6, UC_M68K_REG_A7, UC_M68K_REG_D0, UC_M68K_REG_PC

assert Path('work/ken-verify.bin').read_bytes() == Path('work/ssf2xjr1-ken-dp-ryu.bin').read_bytes()
builds = {
    'original': (Path('work/ssf2xjr1-decrypted.bin').read_bytes(), raw_program('ssf2xjr1.zip')),
    'anterior': (Path('work/ssf2xjr1-fixed.bin').read_bytes(), raw_program('backup/ssf2xjr1-timer-fix.zip')),
    'nova': (Path('work/ssf2xjr1-ken-dp-ryu.bin').read_bytes(), raw_program('work/ken-dp-ryu-enc.zip')),
}
DEF, OPP, FRAME, STOP = 0xff884e, 0xff844e, 0xff9800, 0x300000

def hook_result(build, d_char=0, d_old=0, o_char=4, o_old=0, o_st3=0x0c, o_move=4, o_box=43, prior_2a1=0):
    dec, raw = builds[build]
    e = CPS2(dec, raw); u = e.u
    u.mem_write(DEF + 0x4c, b'\x02'); u.mem_write(DEF + 0x1fd, b'\x00')
    u.mem_write(DEF + 0x391, bytes([d_char])); u.mem_write(DEF + 0x3b6, bytes([d_old]))
    u.mem_write(DEF + 0x39e, struct.pack('>H', OPP & 0xffff)); u.mem_write(DEF + 0x2a1, bytes([prior_2a1]))
    for base in (OPP, 0xffff0000 | (OPP & 0xffff)):
        u.mem_write(base + 0x391, bytes([o_char])); u.mem_write(base + 0x3b6, bytes([o_old]))
        u.mem_write(base + 0x03, bytes([o_st3])); u.mem_write(base + 0x88, bytes([o_move]))
        u.mem_write(base + 0x1a, struct.pack('>I', FRAME))
    u.mem_write(FRAME + 0x0c, bytes([o_box]))
    # run the patched instruction slot at 0x7ad16 only (original: 1 move; new: jsr + hook)
    u.reg_write(UC_M68K_REG_A6, DEF); u.reg_write(UC_M68K_REG_A7, 0xff7000)
    u.emu_start(0x7ad16, 0x7ad1c, count=200)
    return u.mem_read(DEF + 0x1fd, 1)[0], u.mem_read(DEF + 0x2a1, 1)[0]

cases = {
    'ken_dp_hit2_vs_ryu':        (dict(), True),
    'ken_dp_hit1_vs_ryu':        (dict(o_box=55), False),
    'ken_dp_hit3_vs_ryu':        (dict(o_box=44), False),
    'ken_other_special_vs_ryu':  (dict(o_move=2), False),
    'ken_normal_box43_vs_ryu':   (dict(o_st3=0x0a), False),
    'old_ken_vs_ryu':            (dict(o_old=1), False),
    'ryu_attacker_vs_ryu':       (dict(o_char=0), False),
    'ken_dp_hit2_vs_old_ryu':    (dict(d_old=1), False),
    'ken_dp_hit2_vs_ken':        (dict(d_char=4), True),
    'ken_dp_hit2_vs_old_ken':    (dict(d_char=4, d_old=1), False),
    'ken_dp_hit2_vs_chunli':     (dict(d_char=5), False),
    'ken_dp_hit2_vs_fei':        (dict(d_char=14), False),
    'ken_dp_hit2_vs_claw':       (dict(d_char=11), True),
    'ken_dp_hit2_vs_old_claw':   (dict(d_char=11, d_old=1), False),
    'ken_dp_hit2_vs_bison':      (dict(d_char=8), False),
    'ken_dp_hit2_vs_cammy':      (dict(d_char=12), False),
    'ken_dp_hit2_vs_deejay':     (dict(d_char=15), False),
    'ken_dp_hit2_vs_ryu_prior':  (dict(prior_2a1=4), True),
}
res = {}
for name, (kw, changed) in cases.items():
    o, a, n = (hook_result(b, **kw) for b in ('original', 'anterior', 'nova'))
    res[name] = {'original': o, 'anterior': a, 'nova': n}
    assert o == a and n[0] == o[0], (name, o, a, n)          # $1fd copy unchanged
    assert (n[1] == 7) if changed else (n == o), (name, o, n)

def timer(build, helper, dest, i):
    dec, raw = builds[build]
    e = CPS2(dec, raw); u = e.u
    def rnd(u, a, s, d):
        u.reg_write(UC_M68K_REG_D0, i)
        sp = u.reg_read(UC_M68K_REG_A7); u.reg_write(UC_M68K_REG_A7, sp + 4)
        u.reg_write(UC_M68K_REG_PC, int.from_bytes(u.mem_read(sp, 4), 'big'))
    u.hook_add(UC_HOOK_CODE, rnd, begin=0x2e96, end=0x2e96)
    u.reg_write(UC_M68K_REG_A6, OPP); u.reg_write(UC_M68K_REG_A7, 0xff7000)
    u.mem_write(0xff7000, struct.pack('>I', STOP))
    u.emu_start(helper, STOP, count=300)
    return u.mem_read(OPP + dest, 1)[0]
orig = builds['original'][0]
for h in (0x8aeea, 0x8b0aa, 0x8b24a, 0x8b5d8):
    dest = orig[h + 13]
    assert [timer('nova', h, dest, i) for i in range(32)] == [timer('original', h, dest, i) for i in range(32)], hex(h)
res['converted_timer_helpers_identical'] = True
Path('work/ken-dp-ryu-tests.json').write_text(json.dumps(res, indent=2))
for k, v in res.items(): print(k, v)
