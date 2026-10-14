import struct, json, sys
from pathlib import Path
sys.path.insert(0, 'work')
from cps2emu import CPS2, raw_program
from unicorn import UC_HOOK_CODE
from unicorn.m68k_const import UC_M68K_REG_A6, UC_M68K_REG_A7, UC_M68K_REG_D0, UC_M68K_REG_D1, UC_M68K_REG_PC

assert Path('work/rev-verify.bin').read_bytes() == Path('work/ssf2xjr1-reversal.bin').read_bytes()
builds = {
    'original': (Path('work/ssf2xjr1-decrypted.bin').read_bytes(), raw_program('ssf2xjr1.zip')),
    'v0.2': (Path('work/ssf2xjr1-ryu-dp-claw.bin').read_bytes(), raw_program('backup/ssf2xjr1-v0.2.zip')),
    'nova': (Path('work/ssf2xjr1-reversal.bin').read_bytes(), raw_program('work/reversal-enc.zip')),
}
P, STOP = 0xff884e, 0x300000
rb = lambda u, o: u.mem_read(P + o, 1)[0]

def emu(build):
    e = CPS2(*builds[build]); u = e.u
    u.reg_write(UC_M68K_REG_A6, P); return u
def call(u, start, end=None):
    u.reg_write(UC_M68K_REG_A7, 0xff7000); u.mem_write(0xff7000, struct.pack('>I', STOP))
    u.emu_start(start, end or STOP, count=200)

def frame_start(u): call(u, 0x782a0, 0x782a6)      # per-frame clear of $169 (+ buffer aging in the new build)
def record(u):      call(u, 0x45fa)                 # $452a pending path: command finished while unable to act
def wake(u):        call(u, 0x791b6, 0x791bc)       # knockdown wake-up: $16c = 1 (+ buffer check)

def reversal_after(build, n):
    """command finishes n frames before the wake-up frame (n = 0: same frame, the original window)."""
    u = emu(build)
    u.mem_write(P + 0x169, b'\x00'); u.mem_write(P + 0x3f0, b'\x00'); u.mem_write(P + 0x16c, b'\x00')
    frame_start(u); record(u)                       # frame f0
    for _ in range(n):
        frame_start(u)                              # frames f0+1 .. f1 (no new command)
    if n == 0:
        pass
    wake(u)                                         # end of frame f1
    return rb(u, 0x169) == 1 and rb(u, 0x16c) == 1, rb(u, 0x3f0)

res = {'window': {}}
for n in range(0, 11):
    o, v, nw = (reversal_after(b, n)[0] for b in builds)
    res['window'][n] = {'original': o, 'v0.2': v, 'nova': nw}
    assert o == v == (n == 0), (n, o, v)
    assert nw == (n <= 6), (n, nw)

# buffer always consumed at wake-up and never left armed
u = emu('nova'); u.mem_write(P + 0x3f0, b'\x07'); wake(u); assert rb(u, 0x3f0) == 0
u = emu('nova'); u.mem_write(P + 0x3f0, b'\x00'); u.mem_write(P + 0x169, b'\x00'); wake(u); assert rb(u, 0x169) == 0
# per-frame hook keeps d0 = 0 and clears $169 like the original
u = emu('nova'); u.mem_write(P + 0x169, b'\x01'); u.mem_write(P + 0x3f0, b'\x03'); u.reg_write(UC_M68K_REG_D0, 0x55)
frame_start(u); assert rb(u, 0x169) == 0 and rb(u, 0x3f0) == 2 and u.reg_read(UC_M68K_REG_D0) == 0
u = emu('nova'); u.mem_write(P + 0x3f0, b'\x00'); frame_start(u); assert rb(u, 0x3f0) == 0
# record path keeps d1 = 1 (pending result) like the original
u = emu('nova'); record(u); assert u.reg_read(UC_M68K_REG_D1) & 0xff == 1 and rb(u, 0x169) == 1 and rb(u, 0x3f0) == 7
res['hooks_preserve_original_effects'] = True

def timer(build, helper, dest, i):
    u = emu(build)
    def rnd(u, a, s, d):
        u.reg_write(UC_M68K_REG_D0, i)
        sp = u.reg_read(UC_M68K_REG_A7); u.reg_write(UC_M68K_REG_A7, sp + 4)
        u.reg_write(UC_M68K_REG_PC, int.from_bytes(u.mem_read(sp, 4), 'big'))
    u.hook_add(UC_HOOK_CODE, rnd, begin=0x2e96, end=0x2e96)
    call(u, helper)
    return rb(u, dest)
orig = builds['original'][0]
for h in (0x92022, 0x92186, 0x93f2a):
    dest = orig[h + 13]
    assert [timer('nova', h, dest, i) for i in range(32)] == [timer('original', h, dest, i) for i in range(32)], hex(h)
res['converted_timer_helpers_identical'] = True
Path('work/reversal-buffer-tests.json').write_text(json.dumps(res, indent=2))
for n, v in res['window'].items(): print('comando', n, 'frames antes de levantar:', v)
print({k: v for k, v in res.items() if k != 'window'})
