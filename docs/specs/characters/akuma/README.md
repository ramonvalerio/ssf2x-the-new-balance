# Akuma

O Akuma tem uma única versão (id 16, sem versão antiga).

| Spec | Alteração | Status |
|---|---|---|
| [0012](new/0012-teleporte-com-tres-botoes-em-tres-frames.md) | Teleporte com os 3 botões em até 3 frames | Entregue (v0.6) |
| 0013 | Akuma sempre habilitado na seleção de personagem | Em análise (ver nota) |

## Como o Akuma funciona hoje (levantado em 2026-10-14)

- O Akuma é o Ryu (`$391 = 0`) com a flag `$3bd = 1`. Com a flag ligada, os despachantes de golpes usam o id 16 (`0x7b0b4`, índice 16).
- Ele só é liberado por um código secreto na seleção (`0xe83e`): manter o cursor 60 frames em Ryu ou Ken, depois no id 13, no id 3, no id 12, e de novo em Ryu ou Ken. Em seguida, aperta-se Start e faz-se os 3 socos no mesmo frame (`0xe942`). O resultado é `$3bd = 1` e a cor `$3b1 = 10`.
- O retrato grande já tem arte do Akuma: o desenho usa a cor (`$3b1 ≥ 10`) para escolher o conjunto de sprites dele (`0x3c058`).
- No modo arcade, o oponente final Akuma é criado pelo mesmo mecanismo (`0x3a5c`, `0x3a98`).
- A grade de seleção tem 16 posições (8 colunas × 2 linhas) e nenhum ícone do Akuma.
