"""Blanka: rolamento com chute (tras-carga, frente + chute) passa a atravessar o
adversario quando o jogador segura PRA FRENTE no hit confirm, com qualquer forca de
chute (fraco, medio, forte) -- igual ao que ja acontecia naturalmente so com o chute
fraco.

Causa original: o golpe tem um timer interno ($3E, offset do atacante) que comeca
positivo (fase de ida) e fica negativo com o tempo. No hit confirm (0x81bae, dentro do
despachante de fases do golpe em 0x81ad0), so aciona o recuo se esse timer ja estiver
negativo. O chute fraco costuma acertar cedo (ainda positivo = sem recuo = atravessa);
medio e forte acertam tarde (ja negativo = recua) -- o que o jogador descreveu como "o
comportamento do fraco colado".

Mudanca: no hit confirm, alem da checagem original do timer, tambem pula o recuo se o
jogador estiver segurando o direcional de frente (considerando o lado que o Blanka esta
virado, $12(a6)) naquele instante. Segurando pra tras (ou neutro) mantem o
comportamento original, igual a hoje.

Nao muda: qualquer outro golpe ou personagem -- o ponto alterado (0x81bae) fica dentro
do despachante de fases exclusivo deste golpe do Blanka.
"""
import struct
from pathlib import Path

CHUNK_A = 0x80eb2   # helper duplicado em 0x80e9e -> 0x80eae, liberado aqui (20/28 bytes)
CHUNK_B = 0x811fe   # helper duplicado em 0x811ea -> 0x811fa, liberado aqui (18/28 bytes)
PATCH_AT = 0x81bae  # tst.w $3e(a6) ; bpl.b $81bfe  (6 bytes, dentro do hit confirm do golpe)
ORIG_BB4 = 0x81bb4  # sequencia normal (aplica o recuo)
ORIG_BFE = 0x81bfe  # pula o recuo (continua)


def free_table(b, table_addr, shared_addr):
    h = table_addr - 16
    assert b[table_addr:table_addr + 32] == b[shared_addr:shared_addr + 32]
    assert b[h:h + 10] == bytes.fromhex('4eb82e960240001f1d7b') and b[h + 14:h + 16] == bytes.fromhex('4e75')
    dest = b[h + 12:h + 14]
    new = (bytes.fromhex('4eb82e960240001f41fa')
           + struct.pack('>h', shared_addr - (h + 10))
           + bytes.fromhex('1d700000') + dest + bytes.fromhex('4e75'))
    b[h:h + 20] = new
    return table_addr + 4


def bra_w(target, at):
    return bytes.fromhex('6000') + struct.pack('>h', target - (at + 2))


def apply(b, shared_addr=0x80d30):
    """b: bytearray do binario descriptografado (ja com o fix da bola, se houver)."""
    a_table = CHUNK_A - 4
    free_table(b, a_table, shared_addr)
    assert CHUNK_A == a_table + 4

    b_table = CHUNK_B - 4
    free_table(b, b_table, shared_addr)
    assert CHUNK_B == b_table + 4

    chunk_a = (bytes.fromhex('302e0392')      # move.w $392(a6),d0   (le o input atual)
             + bytes.fromhex('4a2e0012')      # tst.b $12(a6)         (virado p/ direita?)
             + bytes.fromhex('6602')          # bne.b +2 (pula o lsr)
             + bytes.fromhex('e248')          # lsr.w #1,d0           (virado p/ esquerda: usa bit de "esquerda")
             + bytes.fromhex('02400001')      # andi.w #1,d0          (isola o bit de frente)
             + bra_w(CHUNK_B, CHUNK_A + 16))  # bra.w CHUNK_B
    assert len(chunk_a) == 20
    b[CHUNK_A:CHUNK_A + 20] = chunk_a

    chunk_b = (bytes.fromhex('4a40')                 # tst.w d0
             + bytes.fromhex('660a')                 # bne.b SKIP (frente segurada -> pula recuo)
             + bytes.fromhex('4a6e003e')              # tst.w $3e(a6)   (comportamento original)
             + bytes.fromhex('6a04')                  # bpl.b SKIP
             + bra_w(ORIG_BB4, CHUNK_B + 10)           # aplica o recuo normalmente
             + bra_w(ORIG_BFE, CHUNK_B + 14))          # SKIP: continua (atravessa)
    assert len(chunk_b) == 18
    b[CHUNK_B:CHUNK_B + 18] = chunk_b

    assert b[PATCH_AT:PATCH_AT + 6] == bytes.fromhex('4a6e003e6a4a'), b[PATCH_AT:PATCH_AT + 6].hex()
    b[PATCH_AT:PATCH_AT + 6] = bytes.fromhex('4ef9') + struct.pack('>I', CHUNK_A)
    return b


def build(base_bin_path='work/ssf2xjr1-decrypted.bin'):
    b = bytearray(Path(base_bin_path).read_bytes())
    apply(b)
    return bytes(b)


if __name__ == '__main__':
    patched = build()
    Path('work/ssf2xjr1-blanka-roll-direction.bin').write_bytes(patched)
    print('ok')
