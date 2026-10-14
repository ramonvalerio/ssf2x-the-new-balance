import sys, struct, json
from pathlib import Path
sys.path.insert(0, 'tools/python')
from unicorn import *
from unicorn.m68k_const import *

base_bin = Path('work/ssf2xjr1-chicken-wing.bin').read_bytes()
assert base_bin[0x951d4:0x951d8] == bytes.fromhex('0c400002')

PATCHES = [
    # Shinken timer helper: read the shared random table at 0x95552 instead of its own copy.
    (0x953dc, '4eb82e960240001f1d7b000a00b1502e00b14e75',
              '4eb82e960240001f41fa016c1d70000000b1502e00b14e75'),
    # Freed space A (old table 0x953f0..0x9540f): window check, part 1.
    (0x953f4, '080809080908080a08080b0d080f09080a0c08080b0809080e0c080a',
              '4eb8452a67120c2e003002b4660a4a2d0dd266046000'
              '02ba4e754e71'),
    # Flame Kick timer helper: same shared table.
    (0x956b0, '4eb82e960240001f1d7b000600954e75',
              '4eb82e960240001f41fafe981d70000000954e75'),
    # Freed space B (old table 0x956c0..0x956df): window check, part 2.
    (0x956c4, '080809080908080a08080b0d080f09080a0c08080b0809080e0c080a',
              '0c2e000c000366124a2e0098660c322e00040241fffd0c4106044e75'),
    # Shinken recognizer: route the move-start check through the new routine.
    (0x953c0, '4eb8452a', '61000032'),
]

def build(src):
    b = bytearray(src)
    for addr, old, new in PATCHES:
        old_b, new_b = bytes.fromhex(old), bytes.fromhex(new)
        assert b[addr:addr + len(old_b)] == old_b, hex(addr)
        assert len(new_b) <= len(old_b) or addr in (0x953dc, 0x956b0), hex(addr)
        b[addr:addr + len(new_b)] = new_b
    return b

patched = build(base_bin)
assert len(patched) == len(base_bin)
changed = [i for i in range(len(base_bin)) if base_bin[i] != patched[i]]
assert all(0x953c0 <= i < 0x95410 or 0x956b0 <= i < 0x956e0 for i in changed)

STOP = 0x300000

def emu(code, a6=0xff844e):
    u = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
    u.ctl_set_cpu_model(UC_CPU_M68K_M68000)
    u.mem_map(0, 0x1000000)
    u.mem_write(0, bytes(code))
    u.reg_write(UC_M68K_REG_A6, a6)
    u.reg_write(UC_M68K_REG_A5, 0xff8000)
    state = {'rand': 0}

    def ret(u):
        sp = u.reg_read(UC_M68K_REG_A7)
        u.reg_write(UC_M68K_REG_A7, sp + 4)
        u.reg_write(UC_M68K_REG_PC, int.from_bytes(u.mem_read(sp, 4), 'big'))

    def hook(u, address, size, data):
        if address == 0x2e96:
            u.reg_write(UC_M68K_REG_D0, state['rand']); ret(u)
        elif address == 0x5b60:
            ret(u)
    u.hook_add(UC_HOOK_CODE, hook)
    return u, state

def call(u, pc):
    u.reg_write(UC_M68K_REG_A7, 0xff7000)
    u.mem_write(0xff7000, struct.pack('>I', STOP))
    u.emu_start(pc, STOP, count=2000)
    assert u.reg_read(UC_M68K_REG_PC) == STOP

def wb(u, addr, v): u.mem_write(addr, bytes([v]))
def rb(u, addr): return u.mem_read(addr, 1)[0]

def shinken_final(code, a6=0xff844e, st3=0x0c, mv=0x00, st4=0x06, st5=0x04,
                  meter=0x30, dd2=0):
    u, _ = emu(code, a6)
    wb(u, a6 + 0x03, st3); wb(u, a6 + 0x98, mv)
    wb(u, a6 + 0x04, st4); wb(u, a6 + 0x05, st5)
    wb(u, a6 + 0x2b4, meter); wb(u, a6 + 0x38e, 1)
    wb(u, 0xff8000 + 0xdd2, dd2)
    wb(u, a6 + 0xb0, 0x0a); wb(u, a6 + 0xb1, 10)
    u.mem_write(a6 + 0x392, struct.pack('>H', 0x0010))  # LP held now
    u.mem_write(a6 + 0x394, struct.pack('>H', 0x0000))  # not held last frame
    call(u, 0x9538c)
    started = rb(u, a6 + 0x98) == 4 and rb(u, a6 + 0x04) == 0 and rb(u, a6 + 0x03) == 0x0c
    return started

results = {}
cases = {
    'rekka2_window_sub4':     dict(st4=6, st5=4),
    'rekka2_window_sub6':     dict(st4=6, st5=6),
    'rekka2_active_sub0':     dict(st4=6, st5=0),
    'rekka2_active_sub2':     dict(st4=6, st5=2),
    'rekka1_window':          dict(st4=4, st5=4),
    'rekka3_window':          dict(st4=8, st5=4),
    'rekka2_meter_not_full':  dict(st4=6, st5=4, meter=0x2f),
    'rekka2_global_freeze':   dict(st4=6, st5=4, dd2=1),
    'flamekick_same_state':   dict(mv=0x02, st4=6, st5=4),
    'neutral_meter_full':     dict(st3=0x00, st4=0, st5=0),
    'neutral_meter_empty':    dict(st3=0x00, st4=0, st5=0, meter=0x10),
}
for name, kw in cases.items():
    for label, code in (('original', base_bin), ('patched', patched)):
        results[f'{label}:{name}'] = shinken_final(code, **kw)
    results[f'patched_p2:{name}'] = shinken_final(patched, a6=0xff884e, **kw)

expect_new = {'rekka2_window_sub4', 'rekka2_window_sub6'}
for name in cases:
    o, p, p2 = results[f'original:{name}'], results[f'patched:{name}'], results[f'patched_p2:{name}']
    assert p == p2, name
    if name in expect_new:
        assert (o, p) == (False, True), (name, o, p)
    else:
        assert o == p, (name, o, p)
assert results['original:neutral_meter_full'] is True
assert results['original:neutral_meter_empty'] is False

# Random timer helpers must produce identical values for every index.
for helper, off in ((0x953dc, 0xb1), (0x956b0, 0x95)):
    for i in range(32):
        vals = []
        for code in (base_bin, patched):
            u, st = emu(code); st['rand'] = i
            call(u, helper)
            vals.append(rb(u, 0xff844e + off))
        assert vals[0] == vals[1], (hex(helper), i, vals)
results['timer_helpers_identical'] = True

Path('work/ssf2xjr1-rekka-super.bin').write_bytes(patched)
Path('work/rekka-super-tests.json').write_text(json.dumps(results, indent=2))
print(json.dumps(results, indent=2))
print('changed bytes:', len(changed))
