"""Blanka: Bola Rolante com soco forte (bf3xx) passa a derrubar qualquer adversario em pe.

Causa: no handler de reacao por tipo de ataque (0xbeeca -> 0xbf0d6, atktype 0x14), quando o
defensor esta em pe (nao agachado, nao no ar) o jogo so grava $2A3(a2) = 3 e deixa $4B(a2)
com o atktype cru (0x14). $4B e o codigo de reacao que decide a queda: golpes que derrubam
(ex.: rasteira, atkid 48) gravam um codigo explicito (0x0E) em $4B; 0x14 nao e um desses
codigos e o defensor so leva hitstun em pe (confirmado por captura: v1 so zerou $2A3 e nao
bastou, $4B continuou 0x14 e sem queda).

Mudanca: quando a caixa de ataque (a3) e exatamente a da bola forte do Blanka (tabela em
0x199988, confirmada contra bytes crus do ROM e contra captura em jogo: atktype=0x14 no
endereco calculado por tbl+id*16 com id=42) e o defensor esta em pe, grava $4B(a2) = 0x0E
(mesmo codigo da rasteira) em vez do atktype cru; $2A3 continua 0, como nos golpes que
derrubam.

Nao muda: qualquer outro golpe, personagem ou atktype == 0x14 de outra entrada de tabela
(a checagem e pelo endereco exato da entrada, nao pelo atktype sozinho).
"""
import sys, struct
from pathlib import Path
sys.path.insert(0, 'tools/python')
from capstone import Cs, CS_ARCH_M68K, CS_MODE_BIG_ENDIAN, CS_MODE_M68K_000

BALL_HP_ENTRY = 0x199988   # tabela de hitbox: bola rolante (soco forte) do Blanka

cs = Cs(CS_ARCH_M68K, CS_MODE_BIG_ENDIAN | CS_MODE_M68K_000)


def free_table(b, table_addr, shared_addr):
    """Aponta o helper de timer logo antes de table_addr para uma tabela idêntica; devolve o espaço liberado."""
    h = table_addr - 16
    assert b[table_addr:table_addr + 32] == b[shared_addr:shared_addr + 32]
    assert b[h:h + 10] == bytes.fromhex('4eb82e960240001f1d7b') and b[h + 14:h + 16] == bytes.fromhex('4e75')
    dest = b[h + 12:h + 14]
    new = (bytes.fromhex('4eb82e960240001f41fa')
           + struct.pack('>h', shared_addr - (h + 10))
           + bytes.fromhex('1d700000') + dest + bytes.fromhex('4e75'))
    b[h:h + 20] = new
    return table_addr + 4


def build(base_bin_path='work/ssf2xjr1-decrypted.bin'):
    b = bytearray(Path(base_bin_path).read_bytes())

    TABLE_ADDR = 0x80f5c   # helper duplicado (idêntico a 0x80d20/0x80e9e/0x811ea)
    SHARED_ADDR = 0x80d30
    HOOK = free_table(b, TABLE_ADDR, SHARED_ADDR)   # 0x80f60, 28 bytes livres

    PATCH_AT = 0xbf0e6
    assert b[PATCH_AT:PATCH_AT + 6] == bytes.fromhex('157c000302a3'), b[PATCH_AT:PATCH_AT + 6].hex()

    # cmpa.l #BALL_HP_ENTRY,a3 ; bne.b SKIP ; move.b #$1c,$4b(a2) ; bra.b DONE
    # SKIP: move.b #3,$2a3(a2) ; DONE: rts
    # $1c = codigo de reacao da cabecada do Honda (atktype 0x1c, mesmo comando:
    # carga tras, frente + soco), deixado sem sobrescrever por aquele golpe --
    # confirmado por captura (react4b=28, hit2a3=0, com o adversario sendo
    # lancado e caindo como pedido).
    hook_code = (bytes.fromhex('b7fc') + struct.pack('>I', BALL_HP_ENTRY)
                 + bytes.fromhex('6608')
                 + bytes.fromhex('157c001c004b')
                 + bytes.fromhex('6006')
                 + bytes.fromhex('157c000302a3')
                 + bytes.fromhex('4e75'))
    assert len(hook_code) == 24, len(hook_code)
    b[HOOK:HOOK + 24] = hook_code

    b[PATCH_AT:PATCH_AT + 6] = bytes.fromhex('4eb9') + struct.pack('>I', HOOK)

    return bytes(b), HOOK


if __name__ == '__main__':
    patched, hook = build()
    Path('work/ssf2xjr1-blanka-ball-knockdown.bin').write_bytes(patched)
    print('hook at', hex(hook))
