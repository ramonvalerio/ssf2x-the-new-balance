# Spec 0018: Blanka — Bola Rolante com soco forte derruba qualquer adversário

Status: Entregue — confirmado no jogo contra o Fei Long (v2)
ADR relacionado: `docs/adr/0007-principios-de-balanceamento.md` (princípio 2: golpes que derrubam devem derrubar em todos os adversários)

## Problema

Bola Rolante do Blanka (trás-carga, frente + soco forte): acerta mas não derruba — o adversário só leva hitstun em pé e se recupera a tempo de levar outra bolada no próximo rolamento.

## Diagnóstico

Capturas em `work/logs/movements-*.csv` (script `work/lua/capture-movements.lua`, campos `react4b`, `curve2a1`, `hit2a3`, `entryaddr` acrescentados durante a investigação).

- A bola usa `atkid=42`, `atktype=0x14`, caixa de ataque na tabela em `0x199988` (confirmado contra os bytes crus da ROM e contra a captura ao vivo).
- A reação a cada tipo de ataque é decidida por um despachante em `0xbeeca` → `0xbf0d6` (tabela por `atktype`, indexada direto pelo valor bruto do byte).
- No caso do atktype 0x14, com o defensor em pé (não agachado, não no ar), o jogo grava `$2A3(a2) = 3` e deixa `$4B(a2)` (código de reação) com o `atktype` cru (0x14) — nenhum dos dois é um código de queda.
- A rasteira (`atkid=48`, atktype `0x0E`) nunca grava `$2A3` (fica 0) e também deixa `$4B` com o atktype cru (0x0E) — mas nesse caso o jogo reconhece 0x0E como código de queda.
- A cabeçada do Honda (trás-carga, frente + soco, `atktype=0x1C`) é o golpe com a animação de queda pedida: lança o adversário bem alto (`y` chega a ~117) e cai. Também deixa `$4B` com o atktype cru (0x1C) — ou seja, 0x1C é reconhecido como código de queda com arco, igual ao pedido.

## Correção

Só para a entrada exata da tabela de hitbox da bola forte do Blanka (`0x199988`), quando o defensor está em pé:
- `$2A3(a2) = 0` (em vez de 3)
- `$4B(a2) = 0x1C` (código de reação da cabeçada do Honda, em vez do atktype cru 0x14)

Implementação: `0x7ad16`-style hook — a instrução original (`move.b #3,$2a3(a2)`, em `0xbf0e6`) foi trocada por `jsr` para uma rotina nova que compara o ponteiro do ataque (`a3`) contra `0x199988` antes de decidir. Espaço liberado convertendo um helper de timer duplicado (`0x80f4c`, técnica do ADR-0006) para ler a tabela compartilhada em `0x80d30`.

Script: `work/blanka_ball_knockdown.py`.

## O que não muda

Qualquer outro golpe, personagem ou entrada da tabela com `atktype=0x14` — a checagem é pelo endereço exato da entrada (`a3`), não pelo atktype sozinho.

## Validação

- Emulação 68000 fiel (Unicorn): confirmado que só a entrada `0x199988` tem `$2A3`/`$4B` alterados; uma entrada vizinha (`+0x10`) fica idêntica ao original.
- Jogo real: Blanka × Fei Long, bola forte derruba (confirmado pelo usuário, v2).

## Histórico de versões

- **v1** (só `$2A3=0`): não bastou — `$4B` continuou com o atktype cru (0x14), sem código de queda reconhecido; o adversário não caía.
- **v2** (`$2A3=0` + `$4B=0x0E`, código da rasteira): derrubou, mas com a animação errada (queda "baixa" da rasteira, não o arco pedido).
- **v3 (entregue)**: `$4B=0x1C` (código da cabeçada do Honda) — queda com arco, igual ao pedido pelo usuário.

Backups da ROM de teste em cada etapa: `backup/ssf2xjr1-blanka-ball-v1-so-2a3.zip`, `backup/ssf2xjr1-blanka-ball-v2-4b0e.zip`.
