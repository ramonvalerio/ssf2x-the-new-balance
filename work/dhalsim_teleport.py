"""Dhalsim (new and old) and Akuma teleport: all 3 punches (or 3 kicks), but spread over up to 3 frames.

The teleport recognizer's last step calls a check routine (new 0x8af1a, old 0x9f11e, Akuma 0xa7fc8, identical, used
only there) with d1 = $70 (punches) or $700 (kicks). Original: Z=1 when ALL buttons of the mask were
pressed on this same frame, or all released on this same frame (negative edge).

New:
- Every frame (the global per-frame hook at 0x93f3a, before the command recognizers) keeps a history
  of newly pressed buttons, packed in one byte (bits 0-2 punches, bits 4-6 kicks):
  $3ea = this frame, $3eb = 1 frame ago, $3f1 = 2 frames ago (bytes unused by the game).
- The check (shared routine T) gives Z=1 when every button of the mask appears in that history, i.e.
  the 3 buttons were pressed within a 3-frame span (the 2nd/3rd up to 2 frames after the 1st).
  The release check (negative edge) stays exactly as the original.
"""
from pathlib import Path

SPAN_FRAMES = 3                         # this frame + the 2 previous frames
base = Path('work/ssf2xjr1-reversal.bin').read_bytes()
TABLE = bytes.fromhex('0a08080b080809080908080a08080b0d080f09080a0c08080b0809080e0c080a')
ORIG = bytes.fromhex('302e03944640c06e0392c041b041670e302e03924640c06e0394c041b0414e75')
G = 0x8dc60
R3 = 0x93f3a                            # per-frame hook from reversal_buffer.py
R3_CODE = bytes.fromhex('70001d4001694a2e03f06704532e03f04e75')
def be16(v): return (v & 0xffff).to_bytes(2, 'big')

b = bytearray(base)
def convert(table_addr):
    h = table_addr - 16
    assert b[h:h + 10] == bytes.fromhex('4eb82e960240001f1d7b') and b[h + 12] == 0 and b[h + 14:h + 16] == bytes.fromhex('4e75'), hex(h)
    assert b[table_addr:table_addr + 32] == TABLE
    dest = b[h + 13]
    b[h:h + 16] = (bytes.fromhex('4eb82e96') + bytes.fromhex('4eb9') + G.to_bytes(4, 'big')
                   + bytes.fromhex('1d40') + bytes([0, dest]) + bytes.fromhex('4e75'))
    return h + 16, h

T1, h1 = convert(0x98542)
T2, h2 = convert(0x986ca)
R4, h4 = convert(0x98828)

def put(addr, code):
    assert len(code) <= 32, (hex(addr), len(code))
    code = code + bytes.fromhex('4e71') * ((32 - len(code)) // 2)
    assert len(code) == 32
    b[addr:addr + 32] = code

# --- per-frame history (R3 is entered by `jsr` from 0x782a0; keeps the original effects at the end) ---
assert b[R3:R3 + len(R3_CODE)] == R3_CODE
put(R3, bytes.fromhex('1d6e03eb03f1')                      # move.b $3eb(a6),$3f1(a6)   2 frames ago
        + bytes.fromhex('1d6e03ea03eb')                    # move.b $3ea(a6),$3eb(a6)   1 frame ago
        + bytes.fromhex('302e0394') + bytes.fromhex('4640') + bytes.fromhex('c06e0392')  # d0 = pressed this frame
        + bytes.fromhex('e848')                            # lsr.w #4,d0
        + bytes.fromhex('02000077')                        # andi.b #$77,d0             punches bits 0-2, kicks 4-6
        + bytes.fromhex('6000') + be16(R4 - (R3 + 30)))    # bra.w R4
put(R4, bytes.fromhex('1d4003ea')                          # move.b d0,$3ea(a6)          this frame
        + R3_CODE)                                         # original per-frame work: d0=0, $169=0, reversal aging, rts

# --- teleport check (shared by new and old Dhalsim) ---
put(T1, bytes.fromhex('102e03ea') + bytes.fromhex('802e03eb') + bytes.fromhex('802e03f1')  # d0 = presses in the last 3 frames
        + bytes.fromhex('3f01')                            # move.w d1,-(sp)
        + bytes.fromhex('e849')                            # lsr.w #4,d1                 mask -> packed bits
        + bytes.fromhex('c001') + bytes.fromhex('b001')    # and.b d1,d0 ; cmp.b d1,d0   all buttons of the mask?
        + bytes.fromhex('4c9f0002')                        # movem.w (sp)+,d1            (flags kept)
        + bytes.fromhex('6700') + be16(T2 + 16 - (T1 + 26))  # beq.w yes (rts with Z=1)
        + bytes.fromhex('6000') + be16(T2 - (T1 + 30)))    # bra.w T2
put(T2, bytes.fromhex('302e0392') + bytes.fromhex('4640') + bytes.fromhex('c06e0394')  # original release check
        + bytes.fromhex('c041') + bytes.fromhex('b041')    # and.w d1,d0 ; cmp.w d1,d0
        + bytes.fromhex('4e75')                            # rts
        + bytes.fromhex('4e75'))                           # T2+16 yes: rts (Z=1 from the press check)
assert b[T2 + 16:T2 + 18] == bytes.fromhex('4e75')

for entry in (0x8af1a, 0x9f11e, 0xa7fc8):
    assert b[entry:entry + 32] == ORIG, hex(entry)
    b[entry:entry + 6] = bytes.fromhex('4ef9') + T1.to_bytes(4, 'big')   # jmp T1 (return address untouched)
assert len(b) == len(base)
Path('work/ssf2xjr1-dhalsim.bin').write_bytes(b)
print('T1', hex(T1), 'T2', hex(T2), 'R4', hex(R4), 'helpers', hex(h1), hex(h2), hex(h4))
