# Spec 0009: Janela de 4 frames para reversal no levantar (global)

Status: Entregue (v0.3 com 6 frames; v0.4 com 4 frames) — pendente de confirmação no jogo
ADRs relacionados: `docs/adr/0007-principios-de-balanceamento.md`, `docs/adr/0006-leituras-de-dados-no-cps2.md`

## Problema

Para sair com um especial ou Super exatamente ao levantar (reversal), o comando precisava terminar **no próprio frame** em que o personagem fica livre. Por isso os jogadores recorrem à técnica do piano: várias bordas de botão para ter mais chances.

## Diagnóstico

- Quando um comando termina com o personagem ainda caído, a checagem `$452a` não deixa o golpe começar. Ela marca o golpe como pendente (`$169 = 1`, em `0x45fa`), e o reconhecedor guarda qual golpe e com que força (`$16A`, `$16B`).
- `$169` é zerado **a cada frame** (`0x782a0`), antes dos reconhecedores.
- No levantar do knockdown (`0x791b6`), o jogo liga `$16C`. A transição para em pé ou agachado chama o despachante de golpe pendente (`0x786d4`), que só executa se `$169` estiver ligado naquele frame.
- Resultado: janela de 1 frame.

## Comportamento novo (regra global, todos os personagens e versões)

Um comando especial ou Super que termine **até 4 frames antes** do levantar sai como reversal no primeiro frame livre, pelo mesmo caminho do jogo. Depois disso, o comando é descartado.

Critério para os 4 frames: com um único botão, o jogador comum passa a ter a mesma chance que um jogador experiente consegue no original usando piano, negative edge e vários toques (algo como 3 a 4 chances seguidas). A v0.3 usava 6 frames; foi reduzida para não deixar o reversal mais fácil do que o teto de execução do original. O comando continua exigindo a execução completa e o botão; só a tolerância de tempo muda.

## Implementação

O byte `$3F0` da estrutura do jogador funciona como contador. Nenhum código do jogo acessa esse byte (varredura de acessos relativos a registrador, a `a5` e absolutos).

| Ponto | Original | Novo |
|---|---|---|
| `0x45fa` (golpe pendente) | `$169 = 1` | `$169 = 1` e `$3F0 = WINDOW + 1` (5) |
| `0x782a0` (início de cada frame) | `$169 = 0` | `$169 = 0` e, se `$3F0 > 0`, `$3F0 = $3F0 - 1` |
| `0x791b6` (levantar do knockdown) | `$16C = 1` | `$16C = 1`; se `$3F0 > 0`, `$169 = 1`; `$3F0 = 0` |

- Código em `0x92032`, `0x92196` e `0x93f3a`. Esse espaço foi liberado convertendo os helpers de timer `0x92022`, `0x92186` e `0x93f2a` para a rotina compartilhada `g`, com os mesmos valores.
- A janela fica em `WINDOW` em `work/reversal_buffer.py`.
- **Fora do escopo:** reversal ao sair de hitstun e de bloqueio (`0x79568`, `0x79664`) continua com a janela original.

## Como testar no jogo

1. Seja derrubado e, ainda no chão, faça o comando de um especial (ex.: Shoryuken) um pouco antes de levantar, apertando o botão uma única vez. O golpe deve sair ao levantar.
2. Faça o comando cedo demais (bem antes de levantar): não deve sair.
3. Confira que levantar sem fazer nada continua normal e que não aparecem golpes "fantasmas".
4. Opcional: o script de captura registra `buf3f0` (contador da janela) para P1 e P2. Ele deve ficar entre 0 e 5 e só mudar quando houver comando com o personagem impedido de agir.

## Validação

- Emulação fiel ao CPS2 (`work/test_reversal_buffer.py`), sequência frame a frame:

  | Comando terminou antes do levantar | Original / v0.2 | Nova |
  |---|---|---|
  | 0 frames | sai | sai |
  | 1 a 4 frames | não sai | sai |
  | 5 frames ou mais | não sai | não sai |

- Os hooks preservam os efeitos originais:
  - `$169` continua sendo zerado a cada frame;
  - `d0 = 0` na volta;
  - o caminho pendente continua devolvendo `d1 = 1`;
  - `$3F0` é sempre consumido no levantar.
- Os 3 helpers convertidos dão os mesmos valores do original.
- A ROM gerada por `tools/build_rom.py` é idêntica à testada.
