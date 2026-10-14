import sys, struct, json
from pathlib import Path
sys.path.insert(0, 'tools/python')
from unicorn import *
from unicorn.m68k_const import *

base_bin = Path('work/ssf2xjr1-rekka-super.bin').read_bytes()

# Ryu (new) Shinku Hadouken recognizer, state 4 (after down, down-forward).
# Original accepts only forward. New: forward -> state 6 (unchanged); down -> state 8,
# so the first quarter circle may end at down-forward (2,3 then 2,3,6 + P).
ADDR = 0x7fc06
OLD = '532e00a167d6302e03a60240000f0c40000266ea542e00a0600000f0'
NEW = ('532e00a1'  # subq.b #1,$a1(a6)
       '67d6'      # beq.b  $7fbe2        timer expired -> reset
       '700f'      # moveq  #$f,d0
       'c06e03a6'  # and.w  $3a6(a6),d0   direction
       '5540'      # subq.w #2,d0         forward -> 0
       '6708'      # beq.b  $7fc1e
       '5540'      # subq.w #2,d0         down -> 0
       '66ea'      # bne.b  $7fc04        anything else: wait (rts)
       '542e00a0'  # addq.b #2,$a0(a6)    down: skip the "down" step
       '6016'      # bra.b  $7fc36        addq.b #2,$a0(a6); bra.w $7fd10 (new timer)
       '4e71')     # nop

patched = bytearray(base_bin)
assert patched[ADDR:ADDR + 28] == bytes.fromhex(OLD)
assert len(bytes.fromhex(NEW)) == 28
patched[ADDR:ADDR + 28] = bytes.fromhex(NEW)
assert patched[0x7fc36:0x7fc3e] == bytes.fromhex('542e00a0600000d4')

STOP = 0x300000
P_LP = 0x0010

def run(code, frames, a6=0xff844e):
    u = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
    u.ctl_set_cpu_model(UC_CPU_M68K_M68000)
    u.mem_map(0, 0x1000000)
    u.mem_write(0, bytes(code))
    u.reg_write(UC_M68K_REG_A5, 0xff8000)

    def ret(u):
        sp = u.reg_read(UC_M68K_REG_A7)
        u.reg_write(UC_M68K_REG_A7, sp + 4)
        u.reg_write(UC_M68K_REG_PC, int.from_bytes(u.mem_read(sp, 4), 'big'))

    def hook(u, address, size, data):
        if address == 0x2e96:
            u.reg_write(UC_M68K_REG_D0, 0); ret(u)
        elif address == 0x5b60:
            ret(u)
    u.hook_add(UC_HOOK_CODE, hook)
    u.mem_write(a6 + 0x38e, b'\x01')
    u.mem_write(a6 + 0x2b4, b'\x30')
    prev = 0
    for direction, buttons in frames:
        u.mem_write(a6 + 0x3a6, struct.pack('>H', direction))
        u.mem_write(a6 + 0x394, struct.pack('>H', prev))
        u.mem_write(a6 + 0x392, struct.pack('>H', buttons))
        prev = buttons
        u.reg_write(UC_M68K_REG_A6, a6)
        u.reg_write(UC_M68K_REG_A7, 0xff7000)
        u.mem_write(0xff7000, struct.pack('>I', STOP))
        u.emu_start(0x7fba8, STOP, count=2000)
        assert u.reg_read(UC_M68K_REG_PC) == STOP
        if u.mem_read(a6 + 0x88, 1)[0] == 8 and u.mem_read(a6 + 0x03, 1)[0] == 0x0c:
            return True
    return False

D, DF, F, DB, B, N = 4, 6, 2, 5, 1, 0
def seq(*dirs, hold=1, press=P_LP):
    frames = [(d, 0) for d in dirs for _ in range(hold)]
    frames[-1] = (frames[-1][0], press)
    return frames

cases = {
    'full_236236P':          (seq(D, DF, F, D, DF, F), True, True),
    'buffered_23_236P':      (seq(D, DF, D, DF, F), False, True),
    'buffered_hold_df':      ([(D, 0), (DF, 0), (DF, 0x200), (DF, 0x200), (DF, 0), (D, 0), (DF, 0), (F, P_LP)], False, True),
    'buffered_slow_3f':      (seq(D, DF, D, DF, F, hold=3), False, True),
    'single_qcf_P':          (seq(D, DF, F), False, False),
    'buffered_no_second_df': (seq(D, DF, D, F), False, False),
    'buffered_no_button':    (seq(D, DF, D, DF, F, press=0), False, False),
    'kick_instead_of_punch': (seq(D, DF, D, DF, F, press=0x100), False, False),
    'junk_back_then_23_236': (seq(D, DF, B, D, DF, F), False, True),
    'downback_after_df':     (seq(D, DF, DB, DF, F), False, False),
    'timeout_on_df':         ([(D, 0)] + [(DF, 0)] * 25 + [(D, 0), (DF, 0), (F, P_LP)], False, False),
}
results = {}
for name, (frames, exp_orig, exp_new) in cases.items():
    o, p = run(base_bin, frames), run(patched, frames)
    p2 = run(patched, frames, a6=0xff884e)
    results[name] = {'original': o, 'patched': p, 'patched_p2': p2}
    assert (o, p, p2) == (exp_orig, exp_new, exp_new), (name, o, p, p2)

Path('work/ssf2xjr1-ryu-super-buffer.bin').write_bytes(patched)
Path('work/ryu-super-buffer-tests.json').write_text(json.dumps(results, indent=2))
print(json.dumps(results, indent=2))
