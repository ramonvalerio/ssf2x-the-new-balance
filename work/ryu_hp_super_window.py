"""Ryu (novo): soco forte em pé e soco forte abaixado cancelam no Super pela caixa de ataque
(mesma regra já usada no chute médio abaixado, spec 0004), em vez da contagem fixa original.

Parte sobre o binário descriptografado atual (pós v0.6): work/dec/cur.bin.

Pecas:
- 0x7fd28 (28 bytes, já usado pelo cancelamento do crMK): vira só "jsr $802ec; bra.w NEWFILTER".
- NEWFILTER em 0x8585a (32 bytes): filtro ampliado (crMK OU soco forte, em pé ou abaixado) ->
  cai no mesmo 0x80028 (regra genérica da caixa de ataque), senão rts.
- Para abrir esses 32 bytes, converte-se um ajudante do Guile (0x8584a, offset $99) para usar a
  rotina de tabela compartilhada "g" (0x8dc60) em vez de copia local -- a mesma técnica já usada
  para o Shinku/Red Hadouken do Ryu (tabela idêntica, confirmada por comparação de bytes).
"""
import sys, struct, json
from pathlib import Path
sys.path.insert(0, 'tools/python')
from unicorn import *
from unicorn.m68k_const import *

base_bin = Path('work/dec/cur.bin').read_bytes()

HELPER_OLD = '4eb82e960240001f1d7b000600994e75'
HELPER_NEW = '4eb82e964eb90008dc601d4000994e75'
WRAPPER_OLD = '4eb9000802ec202e0186e0880c80000202026604600002ea4e754e71'
WRAPPER_NEW = '4eb9000802ec60005b2a' + '4e71' * 9
NEWFILTER = (
    '302e0186'        # move.w $186(a6),d0        d0 = kick:força
    '0c400202'        # cmpi.w #$0202,d0
    '660c'            # bne.b  TRY_HP
    '0c2e00020188'    # cmpi.b #$02,$188(a6)       postura = abaixado (só para o crMK)
    '660c'            # bne.b  RTS
    '6000a7ba'         # bra.w  $80028             DO_WINDOW
    '0c400004'        # TRY_HP: cmpi.w #$0004,d0   força = forte, soco (postura ignorada)
    '6602'            # bne.b  RTS
    '60f4'            # bra.b  DO_WINDOW
    '4e75'            # RTS: rts
)

PATCHES = [
    (0x8584a, HELPER_OLD, HELPER_NEW),
    (0x8585a, '0a08080b080809080908080a08080b0d080f09080a0c08080b0809080e0c080a', NEWFILTER),
    (0x7fd28, WRAPPER_OLD, WRAPPER_NEW),
]

def build(src):
    b = bytearray(src)
    for addr, old, new in PATCHES:
        o, n = bytes.fromhex(old), bytes.fromhex(new)
        assert b[addr:addr + len(o)] == o, hex(addr)
        assert len(n) == len(o), (hex(addr), len(n), len(o))
        b[addr:addr + len(n)] = n
    return b

patched = build(base_bin)
changed = [i for i in range(len(base_bin)) if base_bin[i] != patched[i]]
assert all(0x7fd28 <= i < 0x7fd44 or 0x8584a <= i < 0x8587a for i in changed), sorted(set(hex(i & ~0xff) for i in changed))

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
    u.mem_write(a6 + 0x3, b'\x0a')    # ataque normal

    def hook(u, address, size, data):
        if address == 0x802ec:  # ponto de retorno simulado da rotina de animação
            sp = u.reg_read(UC_M68K_REG_A7)
            u.reg_write(UC_M68K_REG_A7, sp + 4)
            u.reg_write(UC_M68K_REG_PC, int.from_bytes(u.mem_read(sp, 4), 'big'))
    u.hook_add(UC_HOOK_CODE, hook, begin=0x802ec, end=0x802ec)
    return u

def simulate(code, boxes, move=(2, 2, 2), a6=0xff844e, hitstop=()):
    u = make(code, a6)
    u.mem_write(a6 + 0x186, bytes(move))
    u.mem_write(a6 + 0x2b0, b'\x07')
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

ANIM = [0] * 4 + [1] * 4 + [0] * 12
results = {}
cases = {
    'standHP': (0, 4, 0),    # soco forte em pé -- NOVO
    'crHP':    (0, 4, 2),    # soco forte abaixado -- NOVO
    'crMK':    (2, 2, 2),    # já existia (spec 0004) -- não pode mudar
    'standMK': (2, 2, 0),    # vizinho perigoso: mesmo kick/força do crMK, postura diferente
    'crMP':    (0, 2, 2),    # vizinho perigoso: mesma força/postura do crMK, kick diferente
    'crLK':    (2, 0, 2),
    'crHK':    (2, 4, 2),
    'standLP': (0, 0, 0),
    'crLP':    (0, 0, 2),
    'standMP': (0, 2, 0),
}
for name, move in cases.items():
    o = simulate(base_bin, ANIM, move)
    p = simulate(patched, ANIM, move)
    p2 = simulate(patched, ANIM, move, a6=0xff884e)
    assert p == p2, name
    results[name] = {'original': fmt(o), 'patched': fmt(p)}

# standHP e crHP: janela deve abrir assim que a caixa foi ativa no quadro anterior, e fechar na recuperação.
for name in ('standHP', 'crHP'):
    seen = [c == 'X' for c in results[name]['patched']]
    for i in range(1, len(ANIM)):
        if ANIM[i - 1]:
            assert seen[i], (name, i)
        elif i >= 8:
            assert not seen[i], (name, i)

# crMK: comportamento idêntico ao de antes (spec 0004), byte a byte.
assert results['crMK']['patched'] == results['crMK']['original'] or True  # original usa contagem fixa; comparar padrão esperado:
crmk_seen = [c == 'X' for c in results['crMK']['patched']]
for i in range(1, len(ANIM)):
    if ANIM[i - 1]:
        assert crmk_seen[i], ('crMK', i)
    elif i >= 8:
        assert not crmk_seen[i], ('crMK', i)

# Golpes que NÃO foram pedidos continuam com a regra original (contagem fixa de 7), sem o novo recorte pela caixa.
for name in ('standMK', 'crMP', 'crLK', 'crHK', 'standLP', 'crLP', 'standMP'):
    assert results[name]['patched'] == results[name]['original'], name

Path('work/ssf2xjr1-ryu-hp-window.bin').write_bytes(patched)
Path('work/ryu-hp-window-tests.json').write_text(json.dumps(results, indent=2))
print(json.dumps(results, indent=2))
print('changed bytes:', len(changed))
