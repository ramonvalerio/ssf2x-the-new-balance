# ADR-0003: Buffer de comando reaproveitado para cancelar em Super

Status: Superado por ADR-0004 (2026-10-14)
Data: 2026-10-14

## Contexto

Queremos facilitar combos do tipo "normal cancelado em Super", como nos jogos modernos. O exemplo é o ↓ ↘+MK, ↓ ↘ →+P do Ryu.

No jogo original:
- O cancelamento já existe. Quando o normal começa, o jogo liga as flags `$2B0` (Super) e `$195` (especial) por alguns frames. Na época deste ADR, achávamos que elas eram ligadas no contato; o ADR-0004 corrige isso, e a checagem genérica `$452a` passa a aceitar o início do golpe com o personagem em golpe normal (`$3 = $0A`).
- Cada personagem tem uma máquina de estados por comando que avança a cada direção correta. Os reconhecedores rodam todo frame, antes da rotina de ação.
- O que dificulta o combo é a exatidão do comando do Super: o primeiro meia-lua precisa terminar em →, mas no combo ele termina em ↘, onde o normal é apertado.

## Decisão

- Não criar um buffer novo de inputs. Em vez disso, relaxar o passo do reconhecedor do Super que vem logo depois do primeiro ↓ ↘: aceitar ↓ como continuação, pulando o →. Assim, o meia-lua usado no normal é reaproveitado como o primeiro meia-lua do Super.
- Mexer só no reconhecedor do Super do personagem. A regra de quando o cancelamento é permitido (`$2B0`) continua a original.
- Fazer a mudança por personagem, começando pelo Ryu. Cada personagem terá sua própria entrega em `characters/<personagem>/new/`.

## Alternativas descartadas

- **Buffer de botão (repetir a tentativa de início por alguns frames depois de apertar P cedo demais):** é mais próximo dos jogos modernos, mas exige uma flag extra de estado e espaço livre na ROM. Pode virar um ADR futuro se a mudança atual não bastar.
- **Aumentar os timers entre direções:** facilitaria todos os comandos de forma generalizada e mudaria o balanceamento de outros especiais.
- **Liberar o cancelamento mesmo sem contato:** mudaria a regra de jogo, não só a execução.

## Consequências

- O Super também fica mais fácil fora do combo (↓ ↘ ↓ ↘ → + P funciona no neutro).
- A mudança cabe no espaço original do passo (28 bytes), sem precisar de área livre.
- Para outros personagens, é preciso localizar o reconhecedor do Super de cada um (tabela em `0x7b0b4`, índice = id do personagem) e avaliar o passo equivalente. Os comandos variam: carga, meia-lua para trás etc.
