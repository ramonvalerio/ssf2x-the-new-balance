import sys, struct, json
from pathlib import Path
sys.path.insert(0, 'tools/python')
from capstone import *
from unicorn import *
from unicorn.m68k_const import *

base_bin = Path('work/ssf2xjr1-ryu-crmk-window.bin').read_bytes()
TABLE = bytes.fromhex('0a08080b080809080908080a08080b0d080f09080a0c08080b0809080e0c080a')
cs = Cs(CS_ARCH_M68K, CS_MODE_BIG_ENDIAN | CS_MODE_M68K_000)

def be16(v): return (v & 0xffff).to_bytes(2, 'big')

def free_table(b, table_addr, shared_addr):
    """Point the timer helper right before table_addr at an identical table; return freed 28-byte chunk."""
    h = table_addr - 16
    assert b[table_addr:table_addr + 32] == TABLE == b[shared_addr:shared_addr + 32]
    assert b[h:h + 10] == bytes.fromhex('4eb82e960240001f1d7b') and b[h + 14:h + 16] == bytes.fromhex('4e75')
    dest = b[h + 12:h + 14]
    for p in range(table_addr - 0x90, table_addr + 0x90, 2):  # no other pc-relative user of this table
        ins = list(cs.disasm(b[p:p + 10], p, 1))
        if ins and f'${table_addr:x}' in ins[0].op_str:
            assert p == h + 8, hex(p)
    new = bytes.fromhex('4eb82e960240001f41fa') + be16(shared_addr - (h + 10)) + bytes.fromhex('1d700000') + dest + bytes.fromhex('4e75')
    b[h:h + 20] = new
    return table_addr + 4

b = bytearray(base_bin)
A = free_table(b, 0x7fb58, 0x7f9d0)   # Ryu
B = free_table(b, 0x7fe82, 0x7f9d0)   # Ryu
C = free_table(b, 0x852de, 0x85410)   # Ken (helper now reads Ken's identical table)

GO = 0xbf596
code_a = (bytes.fromhex('6706')                              # beq.b  A+8          no vulnerability box -> checks
          + bytes.fromhex('4ef9') + GO.to_bytes(4, 'big')    # jmp    $bf596.l     original path (box present)
          + bytes.fromhex('0c2b0042000b')                    # cmpi.b #$42,$b(a3)  attack type = Ryu Super projectile
          + bytes.fromhex('6604')                            # bne.b  no
          + bytes.fromhex('6000') + be16(B - (A + 18))       # bra.w  B
          + bytes.fromhex('70004e75')                        # no: moveq #0,d0 ; rts
          + bytes.fromhex('4e714e71'))
code_b = (bytes.fromhex('0c2a000e0003')                      # cmpi.b #$0e,$3(a2)  defender in hit state
          + bytes.fromhex('660c')                            # bne.b  no
          + bytes.fromhex('0c2a001c0055')                    # cmpi.b #$1c,$55(a2) falling from air-tatsu knockdown
          + bytes.fromhex('6604')                            # bne.b  no
          + bytes.fromhex('6000') + be16(C - (B + 18))       # bra.w  C
          + bytes.fromhex('70004e75')                        # no
          + bytes.fromhex('4e714e71'))
code_c = (bytes.fromhex('306e0026')                          # movea.w $26(a6),a0  projectile owner
          + bytes.fromhex('4a280391')                        # tst.b  $391(a0)     Ryu = 0
          + bytes.fromhex('660a')                            # bne.b  no
          + bytes.fromhex('7001')                            # moveq  #1,d0        box id 1
          + bytes.fromhex('7204')                            # moveq  #4,d1        vulnerability table 3 (legs)
          + bytes.fromhex('4ef9') + GO.to_bytes(4, 'big')    # jmp    $bf596.l
          + bytes.fromhex('70004e75')                        # no
          + bytes.fromhex('4e714e71'))
for addr, code in ((A, code_a), (B, code_b), (C, code_c)):
    assert len(code) == 28, (hex(addr), len(code))
    b[addr:addr + 28] = code

HOOK = 0xbf562
assert b[0xbf558:0xbf568] == bytes.fromhex('7200286a001a102c00086600003 24e75'.replace(' ', ''))
b[HOOK:HOOK + 6] = bytes.fromhex('4ef9') + A.to_bytes(4, 'big')
patched = b

# ---------- tests ----------
STOP = 0x300000
DEF, PROJ, OWNER = 0xff884e, 0xff9500, 0xff844e
ANIM, BOXTBL, ATK = 0xff9800, 0xff9900, 0xff9a00

def emu(code):
    u = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
    u.ctl_set_cpu_model(UC_CPU_M68K_M68000)
    u.mem_map(0, 0x1000000)
    u.mem_map(0xffff0000, 0x10000)  # 68000 has a 24-bit bus: sign-extended $FFFFxxxx is the same work RAM
    u.mem_write(0, bytes(code))
    u.reg_write(UC_M68K_REG_A5, 0xff8000)
    return u

def ret_hook(u):
    sp = u.reg_read(UC_M68K_REG_A7)
    u.reg_write(UC_M68K_REG_A7, sp + 4)
    u.reg_write(UC_M68K_REG_PC, int.from_bytes(u.mem_read(sp, 4), 'big'))

def vuln(code, boxes=(0, 0, 0), atk_type=0x42, st3=0x0e, r55=0x1c, owner_char=0):
    u = emu(code)
    u.mem_write(DEF + 0x1a, struct.pack('>I', ANIM))
    u.mem_write(ANIM + 8, bytes(boxes))
    u.mem_write(DEF + 0x34, struct.pack('>I', BOXTBL))
    u.mem_write(BOXTBL, struct.pack('>hhhhh', 0x10, 0x20, 0x30, 0x40, 0x50))
    u.mem_write(DEF + 3, bytes([st3])); u.mem_write(DEF + 0x55, bytes([r55]))
    u.mem_write(ATK + 0xb, bytes([atk_type]))
    u.mem_write(PROJ + 0x26, struct.pack('>H', OWNER & 0xffff))
    u.mem_write(OWNER + 0x391, bytes([owner_char])); u.mem_write(0xffff0000 | (OWNER & 0xffff) + 0x391, bytes([owner_char]))
    u.reg_write(UC_M68K_REG_A2, DEF); u.reg_write(UC_M68K_REG_A3, ATK); u.reg_write(UC_M68K_REG_A6, PROJ)
    hits = []
    for entry in (0xbf558, 0xbf568, 0xbf578):
        u.reg_write(UC_M68K_REG_A7, 0xff7000); u.mem_write(0xff7000, struct.pack('>I', STOP))
        u.reg_write(UC_M68K_REG_D0, 0xdead)
        u.emu_start(entry, STOP, count=500)
        found = (u.reg_read(UC_M68K_REG_D0) & 0xff) != 0  # move.b box id / moveq #1
        hits.append((found, hex(u.reg_read(UC_M68K_REG_A4))) if found else (False, None))
    return hits

results = {}
cases = {
    'falling_after_air_tatsu_super_proj': (dict(), True),
    'standing_boxes_present':             (dict(boxes=(1, 1, 1), st3=0, r55=0), False),
    'hitstun_boxes_present':              (dict(boxes=(2, 3, 4), r55=0x1c), False),
    'other_attack_type':                  (dict(atk_type=0x1c), False),
    'hadouken_type_0x3e':                 (dict(atk_type=0x3e), False),
    'defender_not_in_hit_state':          (dict(st3=0x0c), False),
    'other_knockdown_reaction':           (dict(r55=0x3e), False),
    'owner_not_ryu':                      (dict(owner_char=4), False),
}
for name, (kw, new_behavior) in cases.items():
    o, p = vuln(base_bin, **kw), vuln(patched, **kw)
    results[name] = {'original': o, 'patched': p}
    if new_behavior:
        assert o == [(False, None)] * 3, o
        assert p[0][0] is True and p[1] == (False, None) and p[2] == (False, None), p
        assert int(p[0][1], 16) == BOXTBL + 0x30 + 1 * 4, p   # legs table (offset word #3), box id 1
    else:
        assert o == p, (name, o, p)

def timer(code, helper, dest, i):
    u = emu(code)
    def hook(u, address, size, data):
        if address == 0x2e96:
            u.reg_write(UC_M68K_REG_D0, i); ret_hook(u)
    u.hook_add(UC_HOOK_CODE, hook, begin=0x2e96, end=0x2e96)
    u.reg_write(UC_M68K_REG_A6, OWNER)
    u.reg_write(UC_M68K_REG_A7, 0xff7000); u.mem_write(0xff7000, struct.pack('>I', STOP))
    u.emu_start(helper, STOP, count=200)
    return u.mem_read(OWNER + dest, 1)[0]

for tbl in (0x7fb58, 0x7fe82, 0x852de):
    h = tbl - 16; dest = base_bin[h + 13]
    assert all(timer(base_bin, h, dest, i) == timer(patched, h, dest, i) for i in range(32)), hex(tbl)
results['timer_helpers_identical'] = True

changed = [i for i in range(len(base_bin)) if base_bin[i] != patched[i]]
print('changed bytes:', len(changed), 'ranges:', hex(changed[0]), hex(changed[-1]))
Path('work/ssf2xjr1-ryu-air-tatsu-juggle.bin').write_bytes(patched)
Path('work/ryu-air-tatsu-juggle-tests.json').write_text(json.dumps(results, indent=2))
print(json.dumps(results, indent=2))
