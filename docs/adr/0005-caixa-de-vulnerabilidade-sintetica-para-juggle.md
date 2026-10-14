# ADR-0005: Caixa de vulnerabilidade sintética para juggle específico

Status: Aceito (implementado para tatsu aéreo → Super do Ryu em 2026-10-14)
Data: 2026-10-14

## Contexto

No SSF2X, um personagem derrubado não pode ser atingido enquanto cai porque as animações de queda não têm caixas de vulnerabilidade. A regra de juggle em `0xbe708` só trata reações de corpo no ar (`$3E/$44/$48`). Para permitir um juggle específico, é preciso que exista algo a ser atingido.

## Decisão

- Na rotina de colisão de caixas de vulnerabilidade (`0xbf558`, primeira caixa), quando a animação do defensor não tem caixa, usar uma caixa sintética só para a combinação exata pedida: tipo de ataque, estado e reação do defensor e dono do projétil.
- Usar uma caixa já existente da tabela do próprio defensor (id 1 da tabela de pernas), em vez de criar dados novos de hitbox.
- Validar primeiro com captura no jogo (script Lua do FBNeo) e só depois alterar a ROM.

## Alternativas descartadas

- **Mudar as animações de queda para ter caixas:** afetaria todos os golpes que derrubam e todos os personagens.
- **Mudar a regra de juggle `0xbe708`:** não resolve, porque o bloqueio é a falta de caixa e não a regra.

## Consequências

- O padrão serve para outros juggles específicos: trocar tipo de ataque, reação e dono.
- O espaço vem de tabelas aleatórias duplicadas. Cada helper passa a ler uma cópia idêntica (ver ADR-0001 e Specs 0002/0004).
- O ajuste fino da posição da caixa depende de teste no jogo.
