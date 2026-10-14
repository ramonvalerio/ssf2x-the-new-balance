"""Global wake-up reversal buffer.

Original: a special completed while knocked down is only remembered for the current frame ($169 is
cleared every frame at 0x782a2); the wake-up transition (0x791b6) runs it only if the command
finished on that exact frame (1-frame window, hence "piano" inputs).

New: when $452a marks a special as pending (0x45fa), $3f0 (unused by the game) = WINDOW + 1. Every
frame, where the game clears $169 (0x782a0), $3f0 counts down to 0. At the knockdown wake-up (0x791b6),
if $3f0 > 0 the command finished at most WINDOW frames ago: $169 is set again so the game's own
reversal path (0x786d4) runs the stored move ($16a/$16b). $3f0 is cleared at every wake-up.
"""
import sys
from pathlib import Path

WINDOW = 6
base = Path('work/ssf2xjr1-ryu-dp-claw.bin').read_bytes()
TABLE = bytes.fromhex('0a08080b080809080908080a08080b0d080f09080a0c08080b0809080e0c080a')
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

R1, h1 = convert(0x92032)
R2, h2 = convert(0x92196)
R3, h3 = convert(0x93f3a)

# A: record (replaces `move.b #1,$169(a6)` at 0x45fa): command finished while unable to act
ra = (bytes.fromhex('1d7c00010169')            # move.b #1,$169(a6)       original
      + bytes.fromhex('1d7c') + bytes([0, WINDOW + 1]) + bytes.fromhex('03f0')   # move.b #WINDOW+1,$3f0(a6)
      + bytes.fromhex('4e75'))                 # rts
# B: knockdown wake-up (replaces `move.b #1,$16c(a6)` at 0x791b6)
rb = (bytes.fromhex('1d7c0001016c')            # move.b #1,$16c(a6)       original
      + bytes.fromhex('4a2e03f0')              # tst.b $3f0(a6)
      + bytes.fromhex('670a')                  # beq.b done
      + bytes.fromhex('422e03f0')              # clr.b $3f0(a6)            consume
      + bytes.fromhex('1d7c00010169')          # move.b #1,$169(a6)        run the buffered command as reversal
      + bytes.fromhex('4e75'))                 # done: rts
# C: every frame (replaces `moveq #0,d0 ; move.b d0,$169(a6)` at 0x782a0)
rc = (bytes.fromhex('7000')                    # moveq #0,d0              original
      + bytes.fromhex('1d400169')              # move.b d0,$169(a6)       original
      + bytes.fromhex('4a2e03f0')              # tst.b $3f0(a6)
      + bytes.fromhex('6704')                  # beq.b r
      + bytes.fromhex('532e03f0')              # subq.b #1,$3f0(a6)       age the buffered command
      + bytes.fromhex('4e75'))                 # r: rts
for addr, code in ((R1, ra), (R2, rb), (R3, rc)):
    assert len(code) <= 32, (hex(addr), len(code))
    code = code + bytes.fromhex('4e71') * ((32 - len(code)) // 2)
    assert len(code) == 32
    b[addr:addr + 32] = code

for hook, orig, target in ((0x45fa, '1d7c00010169', R1), (0x791b6, '1d7c0001016c', R2), (0x782a0, '70001d400169', R3)):
    assert b[hook:hook + 6] == bytes.fromhex(orig), hex(hook)
    b[hook:hook + 6] = bytes.fromhex('4eb9') + target.to_bytes(4, 'big')
assert len(b) == len(base)
Path('work/ssf2xjr1-reversal.bin').write_bytes(b)
print('chunks', hex(R1), hex(R2), hex(R3), 'helpers', hex(h1), hex(h2), hex(h3))
