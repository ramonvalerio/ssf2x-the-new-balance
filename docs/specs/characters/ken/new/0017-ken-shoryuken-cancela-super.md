# Spec 0017: Ken novo — 2º hit do Shoryuken forte cancela no Super

Status: Entregue (v0.9) — AINDA NÃO TESTADO no jogo
ADR relacionado: `docs/adr/0002-janela-do-segundo-rekka-aceita-super.md` (mesma técnica, aplicada a
outro personagem/golpe)

## Personagem / golpe

Ken novo. Shoryuken forte (`$3 = $0C`, `$88 = 4`).

## Pedido do usuário

"Ken pode cancelar o segundo hit do shory com super para potencializar o combo."

## Comportamento anterior

Como qualquer especial, o Shoryuken bloqueia o Super: a checagem genérica (`$452a`) recusa sempre
que o personagem já está em outro golpe especial (`$3 = $0C`), mesmo com a barra cheia.

## Comportamento novo

Durante o 2º hit do Shoryuken forte (caixa de ataque id 43, a mesma identificada na spec 0006),
com a barra cheia, o comando normal do Super (`236236` + soco) desvia a sequência para o Super em
vez de continuar o Shoryuken. A barra é consumida normalmente.

Fora dessa janela exata (1º ou 3º hit, outro golpe, barra baixa, jogo pausado), nada muda: a
checagem original decide como antes.

## O que não muda

- Os 3 hits do Shoryuken, outros golpes do Ken, Ken antigo, outros personagens.
- Comando, dano e barra do Super fora desse contexto.
- A escolha de força do Super (fraco/médio/forte) continua a cargo do reconhecedor original.

## Implementação

Mesma técnica da spec 0002 (Fei Long Rekka → Super): no despachante de golpes do Ken
(`0x851c0`, chamado a cada frame quando o comando do Super já foi reconhecido e está na fila),
`jsr $452a.w` vira `bsr.w` para uma rotina nova que roda a checagem original e, se ela recusar,
libera uma exceção quando:

- `$88 = 4` (Shoryuken em andamento);
- o quadro de animação atual tem caixa de ataque id `43` (`$2b`, 2º hit — spec 0006);
- `$2B4 = $30` (barra cheia).

Se liberado, a sequência segue para a inicialização normal do Super do Ken (`0x85a22`), a mesma
usada quando o Super sai do neutro.

- Espaço: dois ajudantes de temporização do próprio Ken (destinos `$e9` e `$95`, duplicatas da
  tabela aleatória já compartilhada em `0x8dc60`) foram convertidos para a rotina `g`, liberando
  32 bytes cada — um para a checagem nova, outro para o resto da rotina (dividida em duas partes
  ligadas por um salto, como a tabela de personagem já linkava a Shinku/Red Hadouken do Ryu).
- Script e testes: `work/ken_dp_super_cancel.py`, `work/ken-dp-super-tests.json`.

## Como testar no jogo

1. Feche o emulador. Esta ROM já foi copiada para `Fightcade/emulator/fbneo/ROMs/ssf2xjr1.zip`.
2. Com o Ken novo e a barra cheia, dê soco forte em pé → Shoryuken forte e, durante o 2º hit,
   236236 + soco. O Super deve sair no lugar do 3º hit, conectando o combo.
3. Confira também:
   - Shoryuken completo sem Super, barra cheia ou vazia — os 3 hits devem sair normalmente;
   - comando do Super durante o 1º ou o 3º hit — não deve desviar;
   - comando do Super com a barra vazia durante o 2º hit — Shoryuken continua normal;
   - Super a partir do neutro — continua igual.
4. Teste dos dois lados da tela.

Backups:
- `backup/ssf2xjr1-v0.8.zip`: versão anterior (Fei Long Flame Kick).
- `backup/ssf2xjr1.zip`: original.

## Validação da entrega

- A rotina do despachante foi executada em emulação 68000 isolada (Unicorn) a partir do binário
  real (sem simular `$452a`: o teste força a checagem original a recusar de verdade, via
  `$38e(a6) = 0`, e confere se a exceção libera o Super só no 2º hit com a barra cheia).
- Casos cobertos: 2º hit + barra cheia (deve liberar); 1º hit + barra cheia; 2º hit + barra baixa;
  outro golpe ($88 ≠ 4) com a caixa do 2º hit; neutro sem golpe algum — todos devem continuar
  bloqueados como antes.
- A ROM final foi recriptografada e descriptografada de novo; o resultado corresponde byte a byte
  ao binário pretendido. Mudou só `sfxj.04a` em relação à v0.8.
- AINDA NÃO TESTADO: partida real no Fightcade.

PATCH: a versão completa fica em `patches/v0.9/` e é aplicada sobre a sua própria ROM com:
`python tools/build_rom.py <ssf2xjr1.zip original> <saida.zip>`
Detalhes e hashes: `verification.json`.
