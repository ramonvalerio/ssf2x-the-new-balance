# Spec 0022: Ryu — soco médio e forte em pé acertam adversário agachado colado

Status: Entregue — aplicado na ROM de teste, aguardando confirmação do usuário no jogo
ADR relacionado: `docs/adr/0007-principios-de-balanceamento.md` (princípio 2); mesma classe de inconsistência da Spec 0021 (Fei Long)

## Problema

Mesmo tipo de inconsistência da Spec 0021, pedida pelo usuário para o Ryu: soco médio e soco forte em pé, de perto, no neutro, contra a Cammy agachada.

## Diagnóstico

Captura em `work/logs/movements-20261015-030412.csv`.

- Confirmado: nenhum dos dois golpes conecta (`p2_st3` nunca vai para hitstun).
- Caixa de ataque:
  - Soco médio em pé (atkid 4, ROM `0x198a6c`): `x=-40, y=71, rx=26, ry=13`.
  - Soco forte em pé (atkid 6, ROM `0x198a8c`): `x=-44, y=88, rx=36, ry=20`.
- Caixa de vulnerabilidade da Cammy agachada (mesma de sempre): `x=-67, y=73, rx=21, ry=8`.

### Limitação do modelo (importante)

Tentei validar o tamanho do ajuste reproduzindo a fórmula da rotina de colisão (`0xbf596`–`0xbf654`, desmontada nesta mesma investigação): ela soma os dois `ry` (atacante + defensor) e compara com a distância entre os centros — **não** é uma simples sobreposição de faixas `[y, y+ry]`. Pelo cálculo com essa fórmula, o soco médio do Ryu (`y=71, ry=13`) deveria conectar na Cammy (`y=73, ry=8`): distância = 2, soma dos raios = 21. Ou seja, **o modelo previu acerto onde o jogo mostrou erro** — ainda não bati o motivo exato dessa discrepância (pode ser outro eixo, outra caixa, ou um campo que não é lido do jeito que montei). Isso não impede o ajuste (é reversível e barato de recalibrar), mas o tamanho usado aqui é uma estimativa, não uma conta fechada.

## Correção

Mesma técnica da Spec 0021: edição direta de dado, aumento pequeno (+3, "bem pouquinho", a pedido do usuário) no byte `ry` das duas entradas.

| Golpe | Endereço (ROM, flat) | Arquivo/offset cru | `ry` antes | `ry` depois |
|---|---|---|---|---|
| Soco médio em pé | `0x198a6f` | `sfxj.06a` offset 100974 | 13 | 16 |
| Soco forte em pé | `0x198a8f` | `sfxj.06a` offset 101006 | 20 | 23 |

## O que não muda

Qualquer outro golpe do Ryu (inclusive agachados), qualquer outro personagem, e a caixa de vulnerabilidade da Cammy.

## Como testar no jogo

1. ROM já aplicada em `Fightcade/emulator/fbneo/ROMs/ssf2xjr1.zip` (backup em `backup/ssf2xjr1-antes-ryu-cammy-fix.zip`).
2. Ryu bem colado numa Cammy agachada: soco médio e soco forte em pé devem conectar.
3. Se ainda errar, ou acertar demais (caixa grande demais, pegando coisa que não devia), avisar — o ajuste é só 2 bytes, fácil de recalibrar pra cima ou pra baixo.

## Próximo passo (dívida técnica)

Fechar a conta da rotina de colisão completa (reproduzir em `work/cps2emu.py` ou Unicorn com os valores reais capturados, do jeito que foi feito pro Shoryuken do Ken em `work/ken_dp_reach.py`) antes do próximo ajuste desse tipo, pra não depender de estimativa.
