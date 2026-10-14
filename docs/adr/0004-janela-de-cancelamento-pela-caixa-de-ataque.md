# ADR-0004: Janela de cancelamento definida pela caixa de ataque

Status: Aceito (implementado para o chute médio abaixado do Ryu em 2026-10-14)
Data: 2026-10-14
Substitui: ADR-0003 para o caso do Ryu

## Contexto

A entrada facilitada do ADR-0003 (pular o → do primeiro meia-lua) não resolveu a dificuldade no teste do usuário. O gargalo real é o tempo: o jogo libera o cancelamento para Super por um número fixo de frames a partir do início do normal (7 para o Ryu, em `0x7f018`). Esse contador também é gasto durante o hitstop, então sobra pouca margem depois do contato.

## Decisão

- Para golpes escolhidos, a janela de cancelamento para Super passa a seguir a caixa de ataque da animação: fica aberta enquanto a caixa está ativa e fecha na recuperação.
- A detecção usa o mesmo dado que o visualizador de hitbox do modo treino: o byte `+0x0C` do quadro de animação apontado por `$1A`.
- O filtro é feito por golpe (`$186` botão, `$187` força, `$188` postura), envolvendo a rotina de golpe normal do personagem pela tabela `0x78e18`, sem alterar a rotina comum `0x78dc6`.
- O comando do Super continua o original.

## Alternativas descartadas

- **Aumentar o valor fixo da tabela `0x7f018`:** afetaria todos os normais do personagem e não acompanharia os frames ativos de cada golpe.
- **Liberar também na recuperação:** foi pedido explicitamente que não.

## Consequências

- O cancelamento passa a valer em todos os frames ativos, mesmo que o golpe não acerte. O original também não exigia contato, só que a janela era menor.
- Para repetir isso em outros golpes ou personagens, basta trocar o filtro e a entrada da tabela `0x78e18` (o índice é o id do personagem; os antigos ficam em índice + 0x11).
