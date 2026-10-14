# Spec 0003: Ryu — buffer de comando para o Super (cancelamento facilitado)

Status: Descartado (2026-10-14) — o usuário não conseguiu executar; substituído pela Spec 0004. A entrega em `characters/ryu/new/super-buffer/` fica só como histórico.
ADR relacionado: `docs/adr/0003-buffer-de-comando-reaproveitado.md`

## Personagem / golpe

Ryu novo. Shinku Hadouken (Super).

## Comportamento anterior

O reconhecedor exige ↓ ↘ → ↓ ↘ → + P, nessa ordem, com 16 a 23 frames entre cada direção. No combo ↓ ↘+MK, ↓ ↘ →+P, o primeiro meia-lua termina em ↘ e o comando se perde.

## Comportamento novo

- Depois de ↓ ↘, o reconhecedor aceita → (como antes) ou ↓. O ↓ conta como início do segundo meia-lua.
- Sequências aceitas: ↓ ↘ → ↓ ↘ → + P (original) e ↓ ↘ ↓ ↘ → + P (nova).
- O cancelamento do normal continua dependendo da regra original do jogo (flag `$2B0`, liberada no contato do golpe).

## O que não muda

Tempos entre direções, janela do botão final, barra cheia obrigatória, dano e propriedades do Super, Hadouken e demais especiais, Ryu antigo.

## Implementação

- Reconhecedor do Super do Ryu novo: `0x7fba8` (estado `$A0`, timer `$A1`), chamado a cada frame pela tabela de reconhecedores em `0x7b0b4` (índice 0).
- Passo 3 (`$A0 = 4`), em `0x7fc06–0x7fc21` (28 bytes, reescritos no lugar):
  - → leva ao passo 4, como antes;
  - ↓ leva direto ao passo 5, que espera ↘;
  - qualquer outra direção segue aguardando até o timer acabar, como antes.
- Script e testes: `work/ryu_super_buffer.py`, `work/ryu-super-buffer-tests.json`, `work/package_ryu_super_buffer.py`.
