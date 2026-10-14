"""Fix: timer helpers must read the random table PC-relative (CPS2 decrypts only program-space reads).

Earlier patches made 9 helpers read a shared table through `lea tbl(pc),a0` + `(a0,d0.w)`, which on
CPS2 returns raw encrypted bytes. This rewrites them to call one shared routine `g` that keeps
a PC-relative table, hosted in two standard Sagat helpers whose behaviour is preserved.
"""
import sys, struct, json
from pathlib import Path
sys.path.insert(0, 'tools/python')
from capstone import Cs, CS_ARCH_M68K, CS_MODE_BIG_ENDIAN, CS_MODE_M68K_000

vanilla = Path('work/ssf2xjr1-decrypted.bin').read_bytes()
current = Path('work/ssf2xjr1-ryu-air-tatsu-juggle2.bin').read_bytes()
TABLE = bytes.fromhex('0a08080b080809080908080a08080b0d080f09080a0c08080b0809080e0c080a')

def be16(v): return (v & 0xffff).to_bytes(2, 'big')

H, R2 = 0x8dc5c, 0x8ddb4               # host helpers (dest $85 and $81); tables at +16
G = H + 4
for h, dest in ((H, 0x85), (R2, 0x81)):
    assert current[h:h + 16] == vanilla[h:h + 16] == bytes.fromhex('4eb82e960240001f1d7b0006') + bytes([0, dest]) + bytes.fromhex('4e75')
    assert current[h + 16:h + 48] == TABLE

BROKEN = {  # helper: (dest, has addq #8)
    0x953dc: (0xb1, True), 0x956b0: (0x95, False),
    0x7fd10: (0xa1, True), 0x80014: (0xe1, False), 0x7fb48: (0x99, False), 0x7fe72: (0x95, False),
    0x852ce: (0xe7, False), 0x85574: (0xeb, False), 0x856ca: (0x91, False),
}

b = bytearray(current)
for h, (dest, addq) in BROKEN.items():
    orig = vanilla[h:h + (20 if addq else 16)]
    assert orig[:10] == bytes.fromhex('4eb82e960240001f1d7b') and orig[13] == dest, hex(h)
    assert current[h + 8:h + 10] == bytes.fromhex('41fa'), hex(h)          # the broken lea
    new = (bytes.fromhex('4eb82e96')                                     # jsr $2e96.w
           + bytes.fromhex('4eb9') + G.to_bytes(4, 'big')                # jsr g.l
           + bytes.fromhex('1d40') + bytes([0, dest])                    # move.b d0,$dest(a6)
           + (bytes.fromhex('502e') + bytes([0, dest]) if addq else b'') # addq.b #8,$dest(a6)
           + bytes.fromhex('4e75'))                                      # rts
    assert len(new) == (20 if addq else 16)
    b[h:h + len(new)] = new
    nxt = h + len(new)
    assert b[nxt:nxt + 4] == current[nxt:nxt + 4]                         # untouched gap before patch chunk

W = R2 + 14
host = (bytes.fromhex('6000') + be16(W - (H + 2))                        # bra.w W   (host's own entry)
        + bytes.fromhex('0240001f')                                      # g: andi.w #$1f,d0
        + bytes.fromhex('103b0004')                                      #    move.b tbl(pc,d0.w),d0
        + bytes.fromhex('4e75')                                          #    rts
        + TABLE + bytes.fromhex('4e71'))
assert len(host) == 48
b[H:H + 48] = host
r2 = (bytes.fromhex('4eb82e96') + bytes.fromhex('6100') + be16(G - (R2 + 6))
      + bytes.fromhex('1d400081') + bytes.fromhex('4e75')                # R2's own job: $81
      + bytes.fromhex('4eb82e96') + bytes.fromhex('6100') + be16(G - (W + 6))
      + bytes.fromhex('1d400085') + bytes.fromhex('4e75')                # W: host's job: $85
      + bytes.fromhex('4e71') * 10)
assert len(r2) == 48
b[R2:R2 + 48] = r2

# nothing else may branch into the middle of the host regions
cs = Cs(CS_ARCH_M68K, CS_MODE_BIG_ENDIAN | CS_MODE_M68K_000)
for p in range(H - 0x8000, R2 + 0x8000, 2):
    if H <= p < H + 48 or R2 <= p < R2 + 48:
        continue
    ins = next(cs.disasm(vanilla[p:p + 10], p, 1), None)
    if ins and ins.mnemonic.startswith(('b', 'j', 'lea', 'pea')):
        for t in list(range(H + 2, H + 48, 2)) + list(range(R2 + 2, R2 + 48, 2)):
            assert f'${t:x}' not in ins.op_str.split(',')[0], (hex(p), ins.mnemonic, ins.op_str)

Path('work/ssf2xjr1-fixed.bin').write_bytes(b)
print('ok; changed bytes vs current:', sum(1 for x, y in zip(current, b) if x != y))
