"""Ken (novo): 2º hit do Shoryuken forte cancela no Super (mesma técnica do Rekka->Super do Fei
Long, spec 0002: substitui o jsr $452a.w do despachante de golpes por um bsr que tenta a checagem
original e libera uma exceção quando o 2º hit está ativo e a barra está cheia).

Parte do binário descriptografado atual (pós v0.7/v0.8): work/dec/cur.bin.
"""
import sys, struct, json
from pathlib import Path
sys.path.insert(0, 'tools/python')
from unicorn import *
from unicorn.m68k_const import *

base_bin = Path('work/dec/cur.bin').read_bytes()

CALLSITE_OLD = '4eb8452a'
CALLSITE_NEW = '6100024e'   # bsr.w $85410 (CHUNK_A)

HELPER_A_OLD = '4eb82e960240001f1d7b000600e94e75'
HELPER_A_NEW = '4eb82e964eb90008dc601d4000e94e75'
CHUNK_A = (
    '4eb8452a'        # jsr $452a.w          checagem original
    '6704'            # beq.b SUCCESS
    '60000748'        # bra.w CHUNK_B        (0x85b60)
    '4e75'            # SUCCESS: rts
) + '4e71' * 10        # nop (preenchimento até 32 bytes)

HELPER_B_OLD = '4eb82e960240001f1d7b000600954e75'
HELPER_B_NEW = '4eb82e964eb90008dc601d4000954e75'
CHUNK_B = (
    '0c2e00040088'    # cmpi.b #$4,$88(a6)      golpe atual = Shoryuken
    '6616'            # bne.b FAIL
    '206e001a'        # movea.l $1a(a6),a0      quadro de animação atual
    '0c28002b000c'    # cmpi.b #$2b,$c(a0)      caixa de ataque = id 43 (2º hit, spec 0006)
    '660a'            # bne.b FAIL
    '0c2e003002b4'    # cmpi.b #$30,$2b4(a6)    barra de super cheia
    '6602'            # bne.b FAIL
    '4e75'            # rts (sucesso: Z=1 do ultimo cmpi)
    '4e75'            # FAIL: rts
)

PATCHES = [
    (0x85400, HELPER_A_OLD, HELPER_A_NEW),
    (0x85410, '0a08080b080809080908080a08080b0d080f09080a0c08080b0809080e0c080a', CHUNK_A),
    (0x85b50, HELPER_B_OLD, HELPER_B_NEW),
    (0x85b60, '0a08080b080809080908080a08080b0d080f09080a0c08080b0809080e0c080a', CHUNK_B),
    (0x851c0, CALLSITE_OLD, CALLSITE_NEW),
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
assert all(0x851c0 <= i < 0x851c4 or 0x85400 <= i < 0x85430 or 0x85b50 <= i < 0x85b80 for i in changed), \
    sorted(set(hex(i & ~0xff) for i in changed))

# --- Validação em Unicorn: simula só o despachante (0x851b2 em diante) com $16a=6 (Super enfileirado) ---
STOP = 0x300000

def make(code):
    u = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
    u.ctl_set_cpu_model(UC_CPU_M68K_M68000)
    u.mem_map(0, 0x1000000)
    u.mem_write(0, bytes(code))
    u.reg_write(UC_M68K_REG_A5, 0xff8000)
    # $452a roda de verdade (está inteiro no binário carregado); não precisa de stub. Interceptar a
    # entrada de uma sub-rotina com jsr/rts manual corrompe a pilha neste build do Unicorn.
    return u

def run(code, a6, d88, box_id, bar):
    u = make(code)
    u.mem_write(a6 + 0x16a, b'\x06')   # golpe enfileirado = Super
    u.mem_write(a6 + 0x169, b'\x01')   # há um golpe pendente
    u.mem_write(a6 + 0x88, bytes([d88]))
    u.mem_write(a6 + 0x2b4, bytes([bar]))
    u.mem_write(a6 + 0x38e, b'\x00')   # força o $452a original a recusar (igual ao personagem ocupado no Shoryuken)
    FRAME = 0xff9000
    u.mem_write(FRAME + 0xc, bytes([box_id]))
    u.mem_write(a6 + 0x1a, struct.pack('>I', FRAME))
    u.reg_write(UC_M68K_REG_A6, a6)
    u.reg_write(UC_M68K_REG_A7, 0xff7000)
    u.mem_write(0xff7000, struct.pack('>I', STOP))
    reached = {'tail': False, 'abort': False}
    def mark_tail(u, address, size, data): reached['tail'] = True
    def mark_abort(u, address, size, data): reached['abort'] = True
    u.hook_add(UC_HOOK_CODE, mark_tail, begin=0x85a22, end=0x85a22)
    u.hook_add(UC_HOOK_CODE, mark_abort, begin=0x851e4, end=0x851e4)
    u.emu_start(0x851b2, STOP, count=2000)
    return reached

a6 = 0xff844e
cases = {
    'DP_2o_hit_barra_cheia':    (4, 0x2b, 0x30, True),
    'DP_1o_hit_barra_cheia':    (4, 0x2a, 0x30, False),
    'DP_2o_hit_barra_baixa':    (4, 0x2b, 0x20, False),
    'outro_golpe_2o_hit_barra': (6, 0x2b, 0x30, False),
    'neutro_sem_golpe':         (0, 0x00, 0x30, False),
}
results = {}
for name, (d88, box, bar, expect_super) in cases.items():
    r = run(patched, a6, d88, box, bar)
    results[name] = r
    assert r['tail'] == expect_super and r['abort'] == (not expect_super), (name, r)

Path('work/ssf2xjr1-ken-dp-super.bin').write_bytes(patched)
Path('work/ken-dp-super-tests.json').write_text(json.dumps(results, indent=2))
print(json.dumps(results, indent=2))
print('changed bytes:', len(changed))
