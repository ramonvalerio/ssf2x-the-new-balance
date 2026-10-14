# Spec 0014: Ryu — janela de cancelamento do soco forte (em pé e abaixado) para Super

Status: Entregue (v0.7) — AINDA NÃO TESTADO no jogo
ADR relacionado: `docs/adr/0004-janela-de-cancelamento-pela-caixa-de-ataque.md`
Spec relacionada: `0004-ryu-janela-de-cancelamento-cr-mk.md` (mesma regra, golpe diferente)

## Personagem / golpe

Ryu novo. Soco forte em pé e soco forte abaixado, cancelados no Shinku Hadouken (comando original).

## Pedido do usuário

"O Ryu deve dar soco forte em pé e cancelar com super. Soco forte abaixado e cancelar com super
também com os mesmos frames de acerto menos rigorosos."

Interpretação: os dois socos fortes passam a usar a mesma regra do chute médio abaixado (spec
0004) — janela de cancelamento aberta enquanto a caixa de ataque do quadro atual está ativa, em
vez da contagem fixa original (menos rigorosa porque cobre todo o tempo de acerto, incluindo
hitstop, e não um número fixo de quadros a partir do início do golpe). Não altera os quadros de
acerto (hitbox) do soco forte abaixado em si — isso seria mudança de dados de animação, fora do
escopo pedido.

## Comportamento anterior

Igual ao golpe normal padrão: `0x7f018` define `$2B0 = 7` (7 quadros de janela para Super) e o
valor decresce a cada quadro. O Super só cancela se o comando terminar enquanto `$2B0 ≠ 0`.

## Comportamento novo (soco forte em pé OU abaixado)

- Startup: igual ao original (contagem de 7).
- Enquanto a caixa de ataque do quadro atual está ativa (byte `+0x0C` do quadro `$1A`): Super
  liberado (`$2B0 = $FF`), incluindo hitstop.
- Depois que a caixa some (recuperação): Super bloqueado (`$2B0 = 0`).
- A postura (em pé ou abaixado) não importa para o soco forte — os dois foram pedidos.

## O que não muda

- Chute médio abaixado (spec 0004) continua com a mesma regra, inalterado byte a byte.
- Todos os outros golpes normais do Ryu (fracos, médios, outros fortes) continuam com a contagem
  fixa original.
- Comando do Super, barra, dano, janela de especiais (`$195`). Ryu antigo. Outros personagens.

## Implementação

- `0x7fd28` (mesmo espaço já usado pelo crMK): passa a ser só `jsr $802ec.l` seguido de
  `bra.w` para o novo filtro, com `nop` preenchendo o resto dos 28 bytes disponíveis.
- Filtro novo em `0x8585a` (32 bytes): compara golpe/postura (`$186`/`$187`/`$188`).
  - `kick=2, força=2, postura=2` (chute médio abaixado) → janela pela caixa (regra da spec 0004,
    sem mudança).
  - `kick=0 (soco), força=4 (forte)`, qualquer postura → janela pela caixa (regra nova).
  - Qualquer outra combinação → `rts` (comportamento original intacto).
  - Em ambos os casos de match, cai em `0x80028` (rotina genérica já existente, reutilizada sem
    alteração: ativa/fecha `$2B0` pela caixa de ataque).
- Espaço liberado: os 32 bytes do filtro vieram de uma tabela de temporização duplicada de uma
  rotina do Guile (`0x8584a`, offset de destino `$99`), convertida para usar a rotina
  compartilhada `g` (`0x8dc60`) em vez de ler sua própria cópia local — a mesma técnica já usada
  duas vezes neste projeto (Shinku/Red Hadouken do Ryu, spec 0004). O conteúdo da tabela é
  idêntico byte a byte ao da tabela canônica (`0x8dc68`), confirmado por comparação direta; a
  rotina do Guile foi testada em emulação isolada para os 64 valores de índice possíveis e
  produz exatamente o mesmo resultado antes e depois.
- Script e testes: `work/ryu_hp_super_window.py`, `work/ryu-hp-window-tests.json`.

## Como testar no jogo

1. Feche o emulador (a ROM só é lida ao abrir).
2. Esta ROM já foi copiada para `Fightcade/emulator/fbneo/ROMs/ssf2xjr1.zip`.
3. Com o Ryu novo e a barra cheia, encoste no adversário:
   - soco forte em pé e, logo em seguida, ↓ ↘ → ↓ ↘ → + soco;
   - soco forte abaixado e, logo em seguida, ↓ ↘ → ↓ ↘ → + soco.
4. Confira também:
   - se você terminar o comando na recuperação do golpe (tarde demais), o Super não sai;
   - chute médio abaixado continua cancelando normalmente (spec 0004, não deve ter mudado);
   - os outros normais do Ryu (fracos, médios, chute forte) continuam como antes, sem cancelar
     fora do padrão original;
   - o Ryu do Guile em qualquer luta não deve apresentar nenhuma diferença de comportamento.
5. Teste dos dois lados da tela.

Backups:
- `backup/ssf2xjr1-v0.6.zip`: versão anterior.
- `backup/ssf2xjr1.zip`: original.

## Validação da entrega

- A rotina por frame do golpe normal foi executada em emulação 68000 isolada (Unicorn), comparando
  a ROM anterior (v0.6) com a nova, nas estruturas de memória de P1 e P2, para soco forte em pé,
  soco forte abaixado, chute médio abaixado (controle, deve ficar igual) e sete outros golpes
  vizinhos (chute fraco/forte abaixado, soco médio em pé/abaixado, soco fraco em pé/abaixado,
  chute médio em pé) que devem continuar idênticos ao original.
- A rotina convertida do Guile foi comparada entre a ROM anterior e a nova para os 64 valores
  possíveis do índice de entrada: nenhuma diferença.
- A ROM final foi recriptografada e descriptografada de novo, e o resultado corresponde byte a
  byte ao binário pretendido. Mudaram só `sfxj.03c` e `sfxj.04a`.
- AINDA NÃO TESTADO: partida real no Fightcade.

PATCH: a versão completa fica em `patches/v0.7/` e é aplicada sobre a sua própria ROM com:
`python tools/build_rom.py <ssf2xjr1.zip original> <saida.zip>`
Detalhes e hashes: `verification.json`.
