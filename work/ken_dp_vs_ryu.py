"""Ken (new) fierce Shoryuken vs Ryu/Ken/Claw (new): 2nd hit uses push-back curve 6 instead of heavy curve 2.

Cause (captures + ROM geometry): after hit 2 (attack box 43) Ryu slides with curve 2
(8,8,8,7,...). The 3rd hit (box 44) reaches 53 px in front of Ken on its first active frame;
Ryu's hit-reaction boxes are set back (legs +13, body +33, head +42), so it misses by 4 px.
Curve 1 (6,6,6,5,...) leaves Ryu ~55 px away: 5 px inside the reach.

Hook: defender hit-reaction init 0x7ad16 (a6 = defender). Original `move.b $4c(a6),$1fd(a6)`
is kept; then, only for that exact pair/move/frame, $2a1 = 2 (highest-priority curve override,
read once at 0x78fe0 as index $2a2-1).
"""
import sys, struct, json
from pathlib import Path
sys.path.insert(0, 'work')

base = Path('work/ssf2xjr1-fixed.bin').read_bytes()
TABLE = bytes.fromhex('0a08080b080809080908080a08080b0d080f09080a0c08080b0809080e0c080a')
G = 0x8dc60
def be16(v): return (v & 0xffff).to_bytes(2, 'big')

b = bytearray(base)

def convert(table_addr):
    """Standard timer helper -> jsr $2e96 / jsr g / store / rts. Returns freed 32-byte region."""
    h = table_addr - 16
    assert b[h:h + 10] == bytes.fromhex('4eb82e960240001f1d7b') and b[h + 12] == 0 and b[h + 14:h + 16] == bytes.fromhex('4e75')
    assert b[table_addr:table_addr + 32] == TABLE
    dest = b[h + 13]
    b[h:h + 16] = (bytes.fromhex('4eb82e96') + bytes.fromhex('4eb9') + G.to_bytes(4, 'big')
                   + bytes.fromhex('1d40') + bytes([0, dest]) + bytes.fromhex('4e75'))
    return h + 16, h, dest

C1, h1, d1 = convert(0x8aefa)
C2, h2, d2 = convert(0x8b0ba)
C3, h3, d3 = convert(0x8b25a)
C4, h4, d4 = convert(0x8b5e8)

KEN, CLAW, DP_MOVE, HIT2_BOX, CURVE = 4, 11, 4, 43, 6   # curve 6: 4,4,4,3,3,... (39 px)
# defenders (new version): Ryu (0), Ken (4), Claw (11)
c1 = (bytes.fromhex('1d6e004c01fd')                     # move.b $4c(a6),$1fd(a6)   original instruction
      + bytes.fromhex('102e0391')                       # move.b $391(a6),d0         defender id
      + bytes.fromhex('0c00000b') + bytes.fromhex('6706')  # cmpi.b #11,d0 ; beq.b ok   Claw
      + bytes.fromhex('020000fb') + bytes.fromhex('6604')  # andi.b #$fb,d0 ; bne.b r1  Ryu (0) or Ken (4)
      + bytes.fromhex('6000') + be16(C2 - (C1 + 24))    # ok: bra.w C2
      + bytes.fromhex('4e75')                           # r1: rts
      + bytes.fromhex('4e71') * 2)
c2 = (bytes.fromhex('4a2e03b6') + bytes.fromhex('6616')  # tst.b $3b6(a6) ; bne r2     defender new version
      + bytes.fromhex('306e039e')                       # movea.w $39e(a6),a0         opponent
      + bytes.fromhex('0c280004') + be16(0x391) + bytes.fromhex('660a')   # cmpi.b #4,$391(a0) ; bne r2   Ken
      + bytes.fromhex('4a2803b6') + bytes.fromhex('6604')               # tst.b $3b6(a0) ; bne r2      new
      + bytes.fromhex('6000') + be16(C3 - (C2 + 26))                    # bra.w C3
      + bytes.fromhex('4e75')                                           # r2: rts
      + bytes.fromhex('4e71'))
c3 = (bytes.fromhex('0c28000c0003') + bytes.fromhex('6610')            # cmpi.b #$c,$3(a0) ; bne r3   special move
      + bytes.fromhex('0c2800040088') + bytes.fromhex('6608')           # cmpi.b #4,$88(a0) ; bne r3   Shoryuken
      + bytes.fromhex('2068001a')                                       # movea.l $1a(a0),a0           Ken's frame
      + bytes.fromhex('6000') + be16(C4 - (C3 + 22))                    # bra.w C4
      + bytes.fromhex('4e75')                                           # r3: rts
      + bytes.fromhex('4e71') * 3)
c4 = (bytes.fromhex('0c28002b000c') + bytes.fromhex('6606')           # cmpi.b #43,$c(a0) ; bne r4   2nd-hit box
      + bytes.fromhex('1d7c') + bytes([0, CURVE + 1]) + bytes.fromhex('02a1')  # move.b #7,$2a1(a6)
      + bytes.fromhex('4e75')                                           # r4: rts
      + bytes.fromhex('4e71') * 8)
for addr, code in ((C1, c1), (C2, c2), (C3, c3), (C4, c4)):
    assert len(code) == 32, (hex(addr), len(code))
    b[addr:addr + 32] = code

HOOK = 0x7ad16
assert b[HOOK:HOOK + 6] == bytes.fromhex('1d6e004c01fd')
b[HOOK:HOOK + 6] = bytes.fromhex('4eb9') + C1.to_bytes(4, 'big')
Path('work/ssf2xjr1-ken-dp-ryu.bin').write_bytes(b)
print('regions', hex(C1), hex(C2), hex(C3), hex(C4), 'helpers', hex(h1), hex(h2), hex(h3), hex(h4))
