import sys, struct, json
from pathlib import Path
sys.path.insert(0, 'tools/python')
from unicorn import *
from unicorn.m68k_const import *

# Base: Fei Long changes only (the earlier Ryu input-leniency patch is intentionally not included).
base_bin = Path('work/ssf2xjr1-rekka-super.bin').read_bytes()

PATCHES = [
    # Ryu Shinku Hadouken timer helper: use the identical random table at 0x7f9d0.
    (0x7fd10, '4eb82e960240001f1d7b000a00a1502e00b14e75'.replace('00b14e75', '00a14e75'),
              '4eb82e960240001f41fafcb61d70000000a1502e00a14e75'),
    # Freed space A (old table 0x7fd24..0x7fd43): wrapper around Ryu's normal-attack routine.
    (0x7fd28, '080809080908080a08080b0d080f09080a0c08080b0809080e0c080a',
              '4eb9000802ec'      # jsr    $802ec.l        original Ryu normal-attack routine
              '202e0186'          # move.l $186(a6),d0     $186 kick, $187 strength, $188 posture
              'e088'              # lsr.l  #8,d0
              '0c8000020202'      # cmpi.l #$020202,d0     kick / medium / crouching
              '6604'              # bne.b  rts
              '600002ea'          # bra.w  $80028
              '4e75'              # rts
              '4e71'),            # nop
    # Ryu Red Hadouken timer helper: same shared table.
    (0x80014, '4eb82e960240001f1d7b000600e14e75',
              '4eb82e960240001f41faf9b21d70000000e14e75'),
    # Freed space B (old table 0x80024..0x80043): super-cancel window follows the attack box.
    (0x80028, '080809080908080a08080b0d080f09080a0c08080b0809080e0c080a',
              '206e001a'          # movea.l $1a(a6),a0     current animation frame
              '4a28000c'          # tst.b  $c(a0)          attack box id
              '6706'              # beq.b  inactive
              '50ee02b0'          # st.b   $2b0(a6)        active: window open (negative = set by us)
              '4e75'              # rts
              '4a2e02b0'          # inactive: tst.b $2b0(a6)
              '6a04'              # bpl.b  rts             startup: keep the original countdown
              '422e02b0'          # clr.b  $2b0(a6)        recovery: window closed
              '4e75'),            # rts
    # Normal-attack routine table, Ryu (new): point to the wrapper.
    (0x78e18, '000802ec', '0007fd28'),
]

def build(src):
    b = bytearray(src)
    for addr, old, new in PATCHES:
        o, n = bytes.fromhex(old), bytes.fromhex(new)
        assert b[addr:addr + len(o)] == o, hex(addr)
        b[addr:addr + len(n)] = n
    return b

patched = build(base_bin)
assert patched[0x7f9d0:0x7f9f0] == base_bin[0x7fd24:0x7fd44] == base_bin[0x80024:0x80044]
changed = [i for i in range(len(base_bin)) if base_bin[i] != patched[i]]
assert all(0x78e18 <= i < 0x78e1c or 0x7fd10 <= i < 0x7fd44 or 0x80014 <= i < 0x80044 for i in changed)

STOP = 0x300000
FRAME_ACTIVE, FRAME_IDLE = 0xff9000, 0xff9100

def make(code, a6):
    u = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
    u.ctl_set_cpu_model(UC_CPU_M68K_M68000)
    u.mem_map(0, 0x1000000)
    u.mem_write(0, bytes(code))
    u.reg_write(UC_M68K_REG_A5, 0xff8000)
    u.mem_write(FRAME_ACTIVE + 0xc, b'\x03')
    u.mem_write(FRAME_IDLE + 0xc, b'\x00')
    u.mem_write(a6 + 0x391, b'\x00')  # Ryu
    u.mem_write(a6 + 0x3, b'\x0a')    # normal attack

    def hook(u, address, size, data):
        if address == 0x802ec:  # stand-in for the animation step; return to caller
            sp = u.reg_read(UC_M68K_REG_A7)
            u.reg_write(UC_M68K_REG_A7, sp + 4)
            u.reg_write(UC_M68K_REG_PC, int.from_bytes(u.mem_read(sp, 4), 'big'))
    u.hook_add(UC_HOOK_CODE, hook, begin=0x802ec, end=0x802ec)
    return u

def simulate(code, boxes, move=(2, 2, 2), a6=0xff844e, hitstop=()):
    """Run the normal-attack frame handler once per frame; return cancel-window state seen by the
    command recognizers at the start of each following frame (True = Super cancel allowed)."""
    u = make(code, a6)
    u.mem_write(a6 + 0x186, bytes(move))
    u.mem_write(a6 + 0x2b0, b'\x07')  # set by 0x7f018 when the normal starts (Ryu: 7)
    seen = []
    for i, active in enumerate(boxes):
        seen.append(u.mem_read(a6 + 0x2b0, 1)[0] != 0)
        u.mem_write(a6 + 0x47, bytes([1 if i in hitstop else 0]))
        u.mem_write(a6 + 0x1a, struct.pack('>I', FRAME_ACTIVE if active else FRAME_IDLE))
        u.reg_write(UC_M68K_REG_A6, a6)
        u.reg_write(UC_M68K_REG_A7, 0xff7000)
        u.mem_write(0xff7000, struct.pack('>I', STOP))
        u.emu_start(0x78dc6, STOP, count=5000)
        assert u.reg_read(UC_M68K_REG_PC) == STOP
    return seen

def fmt(seen): return ''.join('X' if s else '.' for s in seen)

# Box pattern after each frame's animation step: 4 startup, 4 active, 12 recovery (shape only).
ANIM = [0] * 4 + [1] * 4 + [0] * 12
results = {}
cases = {
    'crMK':                ((2, 2, 2), ANIM, ()),
    'crMK_long_active':    ((2, 2, 2), [0] * 3 + [1] * 9 + [0] * 10, ()),
    'crMK_hitstop':        ((2, 2, 2), ANIM, range(5, 13)),
    'crLK':                ((2, 0, 2), ANIM, ()),
    'crHK':                ((2, 4, 2), ANIM, ()),
    'standMK':             ((2, 2, 0), ANIM, ()),
    'crMP':                ((0, 2, 2), ANIM, ()),
}
for name, (move, boxes, hs) in cases.items():
    o = simulate(base_bin, boxes, move, hitstop=hs)
    p = simulate(patched, boxes, move, hitstop=hs)
    p2 = simulate(patched, boxes, move, a6=0xff884e, hitstop=hs)
    assert p == p2, name
    results[name] = {'original': fmt(o), 'patched': fmt(p)}
    if move != (2, 2, 2):
        assert o == p, name

crmk = simulate(patched, ANIM)
# Window must cover every frame where the box was active at the end of the previous frame,
# and be closed for every recovery frame.
for i in range(1, len(ANIM)):
    if ANIM[i - 1]:
        assert crmk[i], i
    elif i >= 8:
        assert not crmk[i], i
long_ = simulate(patched, cases['crMK_long_active'][1])
assert all(long_[1:13]) and not any(long_[13:])

Path('work/ssf2xjr1-ryu-crmk-window.bin').write_bytes(patched)
Path('work/ryu-crmk-window-tests.json').write_text(json.dumps(results, indent=2))
print(json.dumps(results, indent=2))
print('changed bytes:', len(changed))
