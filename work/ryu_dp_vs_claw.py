"""Ryu (new): normal attack canceled into fierce Shoryuken vs Claw (new) - Claw's pending push-back becomes curve 6.

Cause (capture movements-20261014-050727.csv): st.HP hits Claw at 36 px; Ryu's fierce DP has its first
active box (43) 4 frames after the st.HP hit-stop ends. During those frames Claw slides with the st.HP
push-back (curve 2) to 74 px, beyond box 43's reach on Claw's hit-reaction boxes (65 px).
With curve 6 Claw stays at ~59-64 px and the Shoryuken connects.

Hook at Ryu-new special start 0x7fb7e (`move.b #$c,$3(a6)`, a6 = Ryu): before the state changes,
if Ryu is canceling a normal ($3 = $0A) into the fierce Shoryuken ($88 = 4, $9b = 4) and the opponent is
Claw new, in hit-stun ($3 = $0E) and still in hit-stop ($47 != 0, slide not started), the opponent's
push-back curve pointer $11a is replaced by curve 6. Nothing else changes.
"""
import sys
from pathlib import Path
sys.path.insert(0, 'work')
from cps2emu import raw_program

base = Path('work/ssf2xjr1-ken-dp-ryu.bin').read_bytes()
raw = raw_program('backup/ssf2xjr1-v0.1.zip')
TABLE = bytes.fromhex('0a08080b080809080908080a08080b0d080f09080a0c08080b0809080e0c080a')
G = 0x8dc60
def be16(v): return (v & 0xffff).to_bytes(2, 'big')

CURVES = 0x79250                      # push-back curve offsets (data, read raw)
CURVE6 = CURVES + int.from_bytes(raw[CURVES + 12:CURVES + 14], 'big', signed=True)
assert list(raw[CURVE6:CURVE6 + 6]) == [4, 4, 4, 3, 3, 3], hex(CURVE6)

b = bytearray(base)
def convert(table_addr):
    h = table_addr - 16
    assert b[h:h + 10] == bytes.fromhex('4eb82e960240001f1d7b') and b[h + 12] == 0 and b[h + 14:h + 16] == bytes.fromhex('4e75'), hex(h)
    assert b[table_addr:table_addr + 32] == TABLE
    dest = b[h + 13]
    b[h:h + 16] = (bytes.fromhex('4eb82e96') + bytes.fromhex('4eb9') + G.to_bytes(4, 'big')
                   + bytes.fromhex('1d40') + bytes([0, dest]) + bytes.fromhex('4e75'))
    return h + 16, h

D1, h1 = convert(0x8df28)
D2, h2 = convert(0x8e08c)
D3, h3 = convert(0x91ec8)
CLAW = 11
DONE = 14                                                               # offset of the original instruction in D3
d1 = (bytes.fromhex('0c2e000a0003') + bytes.fromhex('6610')            # cmpi.b #$a,$3(a6) ; bne done    canceling a normal
      + bytes.fromhex('0c2e00040088') + bytes.fromhex('6608')           # cmpi.b #4,$88(a6) ; bne done    Shoryuken
      + bytes.fromhex('0c2e0004009b') + bytes.fromhex('6704')           # cmpi.b #4,$9b(a6) ; beq cont    fierce
      + bytes.fromhex('6000') + be16(D3 + DONE - (D1 + 26))             # done: bra.w D3+DONE
      + bytes.fromhex('6000') + be16(D2 - (D1 + 30)))                   # cont: bra.w D2
d2 = (bytes.fromhex('306e039e')                                         # movea.w $39e(a6),a0           opponent
      + bytes.fromhex('0c28') + be16(CLAW) + be16(0x391) + bytes.fromhex('6610')  # cmpi.b #11,$391(a0) ; bne done  Claw
      + bytes.fromhex('4a2803b6') + bytes.fromhex('660a')               # tst.b $3b6(a0) ; bne done     new version
      + bytes.fromhex('0c28000e0003')                                   # cmpi.b #$e,$3(a0)            hit-stun
      + bytes.fromhex('6700') + be16(D3 - (D2 + 26))                    # beq.w D3
      + bytes.fromhex('6000') + be16(D3 + DONE - (D2 + 30)))            # done: bra.w D3+DONE
d3 = (bytes.fromhex('4a280047') + bytes.fromhex('6708')                # tst.b $47(a0) ; beq done      still in hit-stop
      + bytes.fromhex('217c') + CURVE6.to_bytes(4, 'big') + be16(0x11a) # move.l #CURVE6,$11a(a0)
      + bytes.fromhex('1d7c000c0003')                                   # done: move.b #$c,$3(a6)      original
      + bytes.fromhex('4e75'))                                          # rts
for addr, code in ((D1, d1), (D2, d2), (D3, d3)):
    assert len(code) <= 32 and (addr != D3 or code[DONE:DONE + 6] == bytes.fromhex('1d7c000c0003')), (hex(addr), len(code))
    code = code + bytes.fromhex('4e71') * ((32 - len(code)) // 2)
    assert len(code) == 32
    b[addr:addr + 32] = code

HOOK = 0x7fb7e
assert b[HOOK:HOOK + 6] == bytes.fromhex('1d7c000c0003')
b[HOOK:HOOK + 6] = bytes.fromhex('4eb9') + D1.to_bytes(4, 'big')
assert len(b) == len(base)
Path('work/ssf2xjr1-ryu-dp-claw.bin').write_bytes(b)
print('chunks', hex(D1), hex(D2), hex(D3), 'helpers', hex(h1), hex(h2), hex(h3), 'curve6', hex(CURVE6))
