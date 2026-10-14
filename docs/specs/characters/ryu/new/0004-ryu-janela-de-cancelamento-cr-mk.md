# Spec 0004: Ryu — janela de cancelamento do chute médio abaixado para Super

Status: Entregue (v0.1) — confirmado no jogo pelo usuário
Substitui: Spec 0003 (descartada)
ADR relacionado: `docs/adr/0004-janela-de-cancelamento-pela-caixa-de-ataque.md`

## Personagem / golpe

Ryu novo. Chute médio abaixado cancelado no Shinku Hadouken (↓ ↘ → ↓ ↘ → + P, comando original).

## Comportamento anterior

Ao iniciar um golpe normal, `0x7f018` define `$2B0 = 7` para o Ryu: 7 frames de janela para Super. A rotina comum de golpe normal (`0x78dc6`) decrementa esse valor a cada frame, inclusive durante o hitstop. O Super só cancela o normal se o comando terminar enquanto `$2B0 ≠ 0` (checagem em `$452a`, `0x45b4`).

## Comportamento novo (só chute médio abaixado)

- Startup: igual ao original (contagem de 7).
- Enquanto o quadro de animação atual tem caixa de ataque (byte `+0x0C` do quadro apontado por `$1A ≠ 0`): Super liberado (`$2B0 = $FF`). Inclui o hitstop, porque a animação fica parada num quadro ativo.
- Depois que a caixa some (recuperação): Super bloqueado (`$2B0 = 0`).

## O que não muda

Comando do Super, barra, dano. Janela de especiais (`$195`). Todos os outros normais do Ryu e dos demais personagens. Ryu antigo.

## Implementação

- `0x78e18`: na tabela de rotinas de golpe normal por personagem, a entrada do Ryu novo passa a apontar para `0x7fd28`.
- `0x7fd28`: chama a rotina original `0x802ec` e filtra o golpe: `$186 = 2` (chute), `$187 = 2` (médio), `$188 = 2` (abaixado).
- `0x80028`: aplica a regra da caixa de ataque. Um valor negativo em `$2B0` marca que a caixa já esteve ativa, para separar startup de recuperação.
- Espaço: tabelas aleatórias duplicadas do Shinku Hadouken e do Red Hadouken passam a usar a cópia idêntica em `0x7f9d0`.
- Script e testes: `work/ryu_crmk_super_window.py`, `work/ryu-crmk-window-tests.json`, `work/package_ryu_crmk_window.py`.

## Como testar no jogo

1. Feche o emulador (a ROM só é lida ao abrir).
2. Esta ROM já foi copiada para Fightcade/emulator/fbneo/ROMs/ssf2xjr1.zip.
3. Abra pelo atalho "SSF2X (teste)".
4. Com o Ryu novo e a barra cheia, encoste no adversário: chute médio abaixado e, logo em seguida, ↓ ↘ → ↓ ↘ → + soco.
   Dica: dá para começar o primeiro meia-lua antes do chute (↓ ↘ + chute médio, → ↓ ↘ → + soco).
5. Confira também:
   - se você terminar o comando na recuperação do chute (tarde demais), o Super não sai;
   - os outros normais do Ryu se comportam como antes.
6. Teste dos dois lados da tela.

Backups:
- backup/ssf2xjr1-ryu-super-buffer.zip: versão anterior, com a entrada facilitada.
- backup/ssf2xjr1-rekka-super.zip: só com as mudanças do Fei Long.
- backup/ssf2xjr1.zip: original.

## Validação da entrega

- A rotina por frame do golpe normal foi executada em emulação 68000 isolada com Unicorn, comparando a ROM anterior com a nova, nas estruturas de memória de P1 e P2.
- No chute médio abaixado, a janela cobre todos os frames ativos, segue aberta no hitstop e fecha na recuperação.
- Chute fraco abaixado, chute forte abaixado, chute médio em pé e soco médio abaixado continuam idênticos ao original.
- A ROM final foi descriptografada novamente e corresponde exatamente ao binário alterado. Mudaram sfxj.03c e sfxj.04a; os demais arquivos são idênticos.
- AINDA NÃO TESTADO: partida real no Fightcade. A emulação usou um padrão de frames de exemplo, não os dados reais da animação do chute.

PATCH: não há mais patches por mudança. A versão completa fica em patches/ (ex.: patches/v0.1/) e é aplicada sobre a sua própria ROM com: python tools/build_rom.py <ssf2xjr1.zip original> <saida.zip>
Detalhes e hashes: verification.json.
