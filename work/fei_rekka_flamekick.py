"""Allow Fei Long's Flame Kick during the third-Rekka input window.

The patch is based on the complete v0.7 decrypted program.  The normal Flame
Kick recognizer still handles direction, kick strength and timing; only its
generic "may a special start now?" gate is extended for the exact state used
after Rekka 2.
"""
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, "tools/python")
from unicorn import UC_ARCH_M68K, UC_HOOK_CODE, UC_MODE_BIG_ENDIAN, Uc
from unicorn.m68k_const import *


BASE_PATH = Path("work/ssf2xjr1-v0.7-decrypted.bin")
OUT_PATH = Path("work/ssf2xjr1-v0.8-decrypted.bin")
TEST_PATH = Path("work/fei-rekka-flamekick-tests.json")

# Two identical random-timer tables are redirected to the already shared table
# at 0x95552.  Their old bytes become small, executable code caves.
PATCHES = [
    # Expand each 16-byte helper to use LEA + address-register indexing.  This
    # consumes four bytes of its old table and frees the remaining 28 bytes.
    (0x964C2,
     "4eb82e960240001f1d7b000600a14e750a08080b",
     "4eb82e960240001f41faf0861d70000000a14e75"),
    (0x989B4,
     "4eb82e960240001f1d7b000600e14e750a08080b",
     "4eb82e960240001f41facb941d70000000e14e75"),

    # Flame Kick final input step: use the extended start check.
    (0x95682, "4eb84542", "61003344"),

    # Part 1 (former timer table): preserve the generic check, then restrict
    # the exception to Fei's Rekka action.  Jump to part 2 with D0 = {$4,$5}.
    (0x989C8,
     "080809080908080a08080b0d080f09080a0c08080b0809080e0c080a",
     "4eb845424a0167120c2e000c0003660a4a2e009866046000daf64e75"),

    # Part 2 (former Rekka timer table): accept only $4=6 and $5 in {4,6}.
    # Clearing bit 1 maps both 0x0604 and 0x0606 to 0x0604.
    (0x964D6,
     "080809080908080a08080b0d080f09080a0c08080b0809080e0c080a",
     "4a2d0dd2660c302e00040240fffd0c4006044e754e714e714e714e71"),
]


def build(src):
    out = bytearray(src)
    for address, old_hex, new_hex in PATCHES:
        old, new = bytes.fromhex(old_hex), bytes.fromhex(new_hex)
        assert len(old) == len(new), hex(address)
        assert out[address:address + len(old)] == old, hex(address)
        out[address:address + len(new)] = new
    return bytes(out)


STOP = 0x300000


def machine(code, a6=0xFF844E):
    u = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
    u.ctl_set_cpu_model(UC_CPU_M68K_M68000)
    u.mem_map(0, 0x1000000)
    u.mem_write(0, code)
    u.reg_write(UC_M68K_REG_A5, 0xFF8000)
    u.reg_write(UC_M68K_REG_A6, a6)

    def do_return():
        sp = u.reg_read(UC_M68K_REG_A7)
        u.reg_write(UC_M68K_REG_A7, sp + 4)
        u.reg_write(UC_M68K_REG_PC, int.from_bytes(u.mem_read(sp, 4), "big"))

    def hook(_u, address, _size, _data):
        if address == 0x2E96:
            _u.reg_write(UC_M68K_REG_D0, 0)
            do_return()
        elif address == 0x5B60:
            do_return()

    u.hook_add(UC_HOOK_CODE, hook)
    return u


def call(u, pc):
    u.reg_write(UC_M68K_REG_A7, 0xFF7000)
    u.mem_write(0xFF7000, struct.pack(">I", STOP))
    u.emu_start(pc, STOP, count=2000)
    assert u.reg_read(UC_M68K_REG_PC) == STOP


def wb(u, address, value):
    u.mem_write(address, bytes([value]))


def rb(u, address):
    return u.mem_read(address, 1)[0]


def flame_final(code, *, a6=0xFF844E, state=0x0C, move=0, step=6,
                substep=4, paused=0, kick=0x400):
    """Run the final Flame Kick recognition stage with a fresh kick press."""
    u = machine(code, a6)
    wb(u, a6 + 0x03, state)
    wb(u, a6 + 0x98, move)
    wb(u, a6 + 0x04, step)
    wb(u, a6 + 0x05, substep)
    wb(u, a6 + 0x38E, 1)
    wb(u, 0xFF8000 + 0xDD2, paused)
    wb(u, a6 + 0x94, 6)       # final Flame Kick command state
    wb(u, a6 + 0x95, 10)      # enough input time remains
    u.mem_write(a6 + 0x392, struct.pack(">H", kick))
    u.mem_write(a6 + 0x394, struct.pack(">H", 0))
    call(u, 0x95632)
    return rb(u, a6 + 0x98) == 2 and rb(u, a6 + 0x04) == 0


base = BASE_PATH.read_bytes()
patched = build(base)

cases = {
    "rekka2_window_sub4": dict(step=6, substep=4),
    "rekka2_window_sub6": dict(step=6, substep=6),
    "rekka2_active_sub0": dict(step=6, substep=0),
    "rekka2_active_sub2": dict(step=6, substep=2),
    "rekka1_window": dict(step=4, substep=4),
    "rekka3_window": dict(step=8, substep=4),
    "other_special": dict(move=2, step=6, substep=4),
    "paused": dict(step=6, substep=4, paused=1),
    "neutral": dict(state=0, step=0, substep=0),
}

results = {}
for name, kwargs in cases.items():
    results[f"v0.7:{name}"] = flame_final(base, **kwargs)
    results[f"v0.8:{name}"] = flame_final(patched, **kwargs)
    results[f"v0.8_p2:{name}"] = flame_final(patched, a6=0xFF884E, **kwargs)

new_cases = {"rekka2_window_sub4", "rekka2_window_sub6"}
for name in cases:
    old = results[f"v0.7:{name}"]
    new = results[f"v0.8:{name}"]
    p2 = results[f"v0.8_p2:{name}"]
    assert new == p2, name
    if name in new_cases:
        assert (old, new) == (False, True), (name, old, new)
    else:
        assert old == new, (name, old, new)

# Strength selection remains the original recognizer's responsibility.
for label, kick in (("LK", 0x100), ("MK", 0x200), ("HK", 0x400)):
    assert flame_final(patched, kick=kick)
    results[f"v0.8:rekka2_{label}"] = True

# Both redirected random timer helpers must remain byte-for-byte equivalent.
for helper, offset in ((0x964C2, 0xA1), (0x989B4, 0xE1)):
    for index in range(32):
        values = []
        for code in (base, patched):
            u = machine(code)
            u.reg_write(UC_M68K_REG_D0, index)
            call(u, helper)
            values.append(rb(u, 0xFF844E + offset))
        assert values[0] == values[1], (hex(helper), index, values)
results["timer_helpers_identical"] = True

OUT_PATH.write_bytes(patched)
TEST_PATH.write_text(json.dumps(results, indent=2), encoding="utf-8")
print(json.dumps(results, indent=2))
print("changed decrypted bytes:", sum(a != b for a, b in zip(base, patched)))
