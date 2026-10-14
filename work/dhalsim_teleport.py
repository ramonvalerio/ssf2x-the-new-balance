"""Dhalsim (new and old) teleport: 2 of the 3 punches (or kicks) at the same time instead of all 3.

The teleport recognizer's last step calls a check routine (new 0x8af1a, old 0x9f11e, identical, used
only there) with d1 = $70 (punches) or $700 (kicks). Original: Z=1 when ALL buttons of the mask were
pressed on this frame, or all released on this frame (negative edge).
New (shared routine T): Z=1 when AT LEAST 2 buttons of the mask were pressed on this frame, or at least
2 released on this frame. 3 still works. Mixed punch+kick does not count (each mask is checked alone).
"""
from pathlib import Path

base = Path('work/ssf2xjr1-reversal.bin').read_bytes()
TABLE = bytes.fromhex('0a08080b080809080908080a08080b0d080f09080a0c08080b0809080e0c080a')
ORIG = bytes.fromhex('302e03944640c06e0392c041b041670e302e03924640c06e0394c041b0414e75')
G = 0x8dc60
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
OK, TWO = T2 + 10, T2 + 14
t1 = (bytes.fromhex('302e0394') + bytes.fromhex('4640') + bytes.fromhex('c06e0392')   # d0 = buttons pressed this frame
      + bytes.fromhex('6100') + be16(TWO - (T1 + 12))                                 # bsr.w two
      + bytes.fromhex('6600') + be16(OK - (T1 + 16))                                  # bne.w ok
      + bytes.fromhex('302e0392') + bytes.fromhex('4640') + bytes.fromhex('c06e0394') # d0 = buttons released this frame
      + bytes.fromhex('6000') + be16(T2 - (T1 + 30)))                                 # bra.w T2
t2 = (bytes.fromhex('6100') + be16(TWO - (T2 + 2))                                    # bsr.w two
      + bytes.fromhex('6604')                                                         # bne.b ok
      + bytes.fromhex('7001') + bytes.fromhex('4e75')                                 # moveq #1,d0 ; rts   (Z=0: no)
      + bytes.fromhex('7000') + bytes.fromhex('4e75')                                 # ok: moveq #0,d0 ; rts (Z=1: yes)
      + bytes.fromhex('c041')                                                         # two: and.w d1,d0     buttons of this mask
      + bytes.fromhex('3f01')                                                         #      move.w d1,-(sp)
      + bytes.fromhex('3200') + bytes.fromhex('5341') + bytes.fromhex('c240')         #      d1 = d0 & (d0-1): != 0 if >= 2 bits
      + bytes.fromhex('4c9f0002')                                                     #      movem.w (sp)+,d1 (flags kept)
      + bytes.fromhex('4e75'))                                                        #      rts
assert t2[10:14] == bytes.fromhex('70004e75') and t2[14:16] == bytes.fromhex('c041')
for addr, code in ((T1, t1), (T2, t2)):
    assert len(code) <= 32, (hex(addr), len(code))
    code = code + bytes.fromhex('4e71') * ((32 - len(code)) // 2)
    assert len(code) == 32
    b[addr:addr + 32] = code

for entry in (0x8af1a, 0x9f11e):
    assert b[entry:entry + 32] == ORIG, hex(entry)
    b[entry:entry + 6] = bytes.fromhex('4ef9') + T1.to_bytes(4, 'big')               # jmp T1 (return address untouched)
assert len(b) == len(base)
Path('work/ssf2xjr1-dhalsim.bin').write_bytes(b)
print('T1', hex(T1), 'T2', hex(T2), 'helpers', hex(h1), hex(h2))
