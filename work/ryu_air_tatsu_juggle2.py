import sys, struct, json
from pathlib import Path
sys.path.insert(0, 'tools/python')
from unicorn import *
from unicorn.m68k_const import *

src = open('work/ryu_air_tatsu_juggle.py', encoding='utf-8').read().split('results = {}')[0]
g = {}
exec(compile(src, 'ryu_air_tatsu_juggle', 'exec'), g)
prev = bytes(g['patched'])          # ROM with the 1-hit juggle
b = bytearray(prev)
A, B, C = g['A'], g['B'], g['C']
be16 = g['be16']

GROUND_Y = 0x28                     # captured: standing y = 40
LOW_LIMIT = GROUND_Y + 24           # follow-up hits only at or below this height

D = g['free_table'](b, 0x85584, 0x85410)   # Ken, identical table
E = g['free_table'](b, 0x856da, 0x85410)   # Ken, identical table

code_b = (bytes.fromhex('0c2a000e0003')                      # cmpi.b #$0e,$3(a2)  defender in hit state
          + bytes.fromhex('660e')                            # bne.b  no
          + bytes.fromhex('0c2a001c0055')                    # cmpi.b #$1c,$55(a2) air-tatsu knockdown -> 1st-hit rule
          + bytes.fromhex('6700') + be16(D - (B + 16))       # beq.w  D
          + bytes.fromhex('6000') + be16(E - (B + 20))       # bra.w  E            later hits -> height rule
          + bytes.fromhex('70004e75')                        # no: moveq #0,d0 ; rts
          + bytes.fromhex('4e71'))
code_d = (bytes.fromhex('0c2a00040005')                      # cmpi.b #4,$5(a2)    still falling (not landed/bouncing)
          + bytes.fromhex('6604')                            # bne.b  no
          + bytes.fromhex('6000') + be16(C - (D + 10))       # bra.w  C
          + bytes.fromhex('70004e75')                        # no
          + bytes.fromhex('4e714e714e714e714e714e71'))
code_e = (bytes.fromhex('0c6a') + be16(LOW_LIMIT) + bytes.fromhex('000a')  # cmpi.w #LOW_LIMIT,$a(a2)
          + bytes.fromhex('6e0c')                            # bgt.b  no           too high
          + bytes.fromhex('0c6a') + be16(GROUND_Y) + bytes.fromhex('000a')   # cmpi.w #GROUND_Y,$a(a2)
          + bytes.fromhex('6f04')                            # ble.b  no           on the ground
          + bytes.fromhex('6000') + be16(C - (E + 18))       # bra.w  C
          + bytes.fromhex('70004e75')                        # no
          + bytes.fromhex('4e714e71'))
for addr, code in ((B, code_b), (D, code_d), (E, code_e)):
    assert len(code) == 28, (hex(addr), len(code))
    b[addr:addr + 28] = code
patched = b

# ---------- tests ----------
DEF, PROJ, OWNER, ANIM, BOXTBL, ATK, STOP = (g[k] for k in ('DEF', 'PROJ', 'OWNER', 'ANIM', 'BOXTBL', 'ATK', 'STOP'))

def vuln(code, r55, y, boxes=(0, 0, 0), atk_type=0x42, st3=0x0e, owner_char=0, st5=4):
    u = g['emu'](code)
    u.mem_write(DEF + 0x1a, struct.pack('>I', ANIM)); u.mem_write(ANIM + 8, bytes(boxes))
    u.mem_write(DEF + 0x34, struct.pack('>I', BOXTBL))
    u.mem_write(BOXTBL, struct.pack('>hhhhh', 0x10, 0x20, 0x30, 0x40, 0x50))
    u.mem_write(DEF + 3, bytes([st3])); u.mem_write(DEF + 0x55, bytes([r55])); u.mem_write(DEF + 5, bytes([st5]))
    u.mem_write(DEF + 0x0a, struct.pack('>h', y))
    u.mem_write(ATK + 0xb, bytes([atk_type]))
    u.mem_write(PROJ + 0x26, struct.pack('>H', OWNER & 0xffff))
    u.mem_write(0xffff0000 | (OWNER & 0xffff) + 0x391, bytes([owner_char]))
    u.reg_write(UC_M68K_REG_A2, DEF); u.reg_write(UC_M68K_REG_A3, ATK); u.reg_write(UC_M68K_REG_A6, PROJ)
    u.reg_write(UC_M68K_REG_A7, 0xff7000); u.mem_write(0xff7000, struct.pack('>I', STOP))
    u.reg_write(UC_M68K_REG_D0, 0xdead)
    u.emu_start(0xbf558, STOP, count=500)
    return (u.reg_read(UC_M68K_REG_D0) & 0xff) != 0

FOLLOW = 0x42   # reaction after a Super hit (any value other than $1C goes through the height rule)
cases = [
    # name, kwargs, expected 1-hit build, expected new build
    ('first_hit_high',        dict(r55=0x1c, y=110), True,  True),
    ('first_hit_low',         dict(r55=0x1c, y=50),  True,  True),
    ('followup_high',         dict(r55=FOLLOW, y=100), False, False),
    ('followup_just_above',   dict(r55=FOLLOW, y=LOW_LIMIT + 1), False, False),
    ('followup_at_limit',     dict(r55=FOLLOW, y=LOW_LIMIT), False, True),
    ('followup_low',          dict(r55=FOLLOW, y=45), False, True),
    ('followup_other_react',  dict(r55=0x3e, y=45), False, True),
    ('low_but_not_hit_state', dict(r55=FOLLOW, y=45, st3=0x0c), False, False),
    ('low_other_attack',      dict(r55=FOLLOW, y=45, atk_type=0x1c), False, False),
    ('low_owner_not_ryu',     dict(r55=FOLLOW, y=45, owner_char=4), False, False),
    ('first_hit_on_bounce',   dict(r55=0x1c, y=48, st5=8), True,  False),
    ('first_hit_landed',      dict(r55=0x1c, y=40, st5=6), True,  False),
    ('followup_on_ground',    dict(r55=FOLLOW, y=GROUND_Y), False, False),
    ('real_boxes_present',    dict(r55=FOLLOW, y=100, boxes=(1, 1, 1)), True, True),
]
results = {}
for name, kw, exp_prev, exp_new in cases:
    o, p = vuln(prev, **kw), vuln(patched, **kw)
    p_vanilla_like = vuln(bytes(g['base_bin']), **kw)
    results[name] = {'before_1hit_build': o, 'patched': p, 'without_juggle': p_vanilla_like}
    assert (o, p) == (exp_prev, exp_new), (name, o, p)

def timer(code, helper, dest, i):
    u = g['emu'](code)
    def hook(u, address, size, data):
        if address == 0x2e96:
            u.reg_write(UC_M68K_REG_D0, i); g['ret_hook'](u)
    u.hook_add(UC_HOOK_CODE, hook, begin=0x2e96, end=0x2e96)
    u.reg_write(UC_M68K_REG_A6, OWNER)
    u.reg_write(UC_M68K_REG_A7, 0xff7000); u.mem_write(0xff7000, struct.pack('>I', STOP))
    u.emu_start(helper, STOP, count=200)
    return u.mem_read(OWNER + dest, 1)[0]
for t in (0x85584, 0x856da):
    h = t - 16; dest = prev[h + 13]
    assert all(timer(prev, h, dest, i) == timer(patched, h, dest, i) for i in range(32)), hex(t)
results['timer_helper_identical'] = True

Path('work/ssf2xjr1-ryu-air-tatsu-juggle2.bin').write_bytes(patched)
Path('work/ryu-air-tatsu-juggle2-tests.json').write_text(json.dumps(results, indent=2))
print(json.dumps(results, indent=2))
