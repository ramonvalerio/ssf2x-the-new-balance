# Spec 0004: Ryu — janela de cancelamento do chute médio abaixado para Super

Status: Entregue — `characters/ryu/new/crmk-super-cancel-window/` (pendente: teste em partida real no Fightcade)
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
