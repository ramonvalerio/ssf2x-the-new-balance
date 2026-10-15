# Spec 0021: Fei Long — soco fraco e médio em pé acertam a Cammy agachada colada

Status: Entregue — aplicado na ROM de teste, aguardando confirmação do usuário no jogo
ADR relacionado: `docs/adr/0007-principios-de-balanceamento.md` (princípio 2: inconsistências de conexão devem ser corrigidas)

## Problema

Fei Long perto e de pé, Cammy agachada: soco fraco em pé e soco médio em pé erram o golpe (não conectam), mesmo colado.

## Diagnóstico

Captura em `work/logs/movements-20261015-023135.csv` (script `work/lua/capture-movements.lua`, campos de geometria de caixa `atkgx/atkgy/atkgrx/atkgry` e `vg8x/vg8y/vg8rx/vg8ry` acrescentados durante a investigação).

- Confirmado: nenhum dos dois golpes conecta (`p2_st3` nunca vai para hitstun durante as tentativas).
- Caixa de ataque (tabela de hitbox, offsets x/y/rx/ry):
  - Soco fraco em pé (atkid 2, ROM `0x19eb36`): `x=-41, y=67, rx=24, ry=7`.
  - Soco médio em pé (atkid 3, ROM `0x19eb46`): `x=-46, y=67, rx=30, ry=10`.
- Caixa de vulnerabilidade da Cammy agachada (box id 17, mesma id pras "pernas/corpo/cabeça" enquanto agachada): `x=-67, y=73, rx=21, ry=8`.
- A rotina de colisão (`0xbf596`–`0xbf654`) não é um teste de sobreposição simples; o modelo exato não foi totalmente validado nesta investigação (ver "Limitação" abaixo). Na prática, o `y=67` do Fei Long é visivelmente menor que o `y=73` da Cammy agachada, e o `ry` pequeno (7/10) deixa pouca margem vertical — consistente com um quase-acerto que erra por poucos pixels.

## Correção

Edição direta de dado (sem patch de código): aumenta o byte `ry` (alcance vertical) das duas entradas em +6.

| Golpe | Endereço (ROM, flat) | Arquivo/offset cru | `ry` antes | `ry` depois |
|---|---|---|---|---|
| Soco fraco em pé | `0x19eb39` | `sfxj.06a` offset 125752 | 7 | 13 |
| Soco médio em pé | `0x19eb49` | `sfxj.06a` offset 125768 | 10 | 16 |

Script: `work/blanka_ball_knockdown.py`-style edição direta nos bytes crus do ROM (sem precisar de criptografia, por ser dado puro, não código — ver ADR-0006). Nenhuma rotina de código foi tocada.

## O que não muda

Qualquer outro golpe do Fei Long (inclusive os agachados), qualquer outro personagem, e a caixa de vulnerabilidade da Cammy (não foi alterada — só a caixa de ataque do Fei Long).

## Limitação / próximo passo

O tamanho exato do ajuste (+6) foi estimado a partir da geometria capturada, não de uma simulação completa da rotina de colisão (que usa uma fórmula mais complexa que uma simples sobreposição de faixas — ver spec 0022 do Ryu para detalhes). Se o teste no jogo mostrar que ainda erra, ou que passou a acertar outra coisa que não devia, o ajuste é só esses 2 bytes — fácil de recalibrar.

## Como testar no jogo

1. ROM já aplicada em `Fightcade/emulator/fbneo/ROMs/ssf2xjr1.zip` (backup da versão anterior em `backup/ssf2xjr1-antes-fei-cammy-fix.zip`).
2. Fei Long bem colado numa Cammy agachada: soco fraco em pé e soco médio em pé devem conectar.
3. Conferir que golpes agachados do Fei Long e o jogo contra outros personagens continuam iguais.
