# Spec 0003: Ryu — buffer de comando para o Super (cancelamento facilitado)

Status: Descartado (2026-10-14) — o usuário não conseguiu executar; substituído pela Spec 0004. Não incluído em nenhuma versão.
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

## Como testar no jogo

1. Feche o emulador (se estiver aberto, a ROM antiga continua carregada na memória).
2. Esta ROM já foi copiada para Fightcade/emulator/fbneo/ROMs/ssf2xjr1.zip.
3. Abra Fightcade/emulator/fbneo/fcadefbneo.exe e carregue ssf2xjr1.
4. Com o Ryu novo e a barra cheia, encoste no adversário e faça: ↓ ↘ + chute médio, ↓ ↘ → + soco.
5. Confira também que ↓ ↘ → ↓ ↘ → + soco continua funcionando e que ↓ ↘ → + soco sozinho continua sendo Hadouken.
6. Teste dos dois lados da tela.

Backups:
- backup/ssf2xjr1-rekka-super.zip: ROM anterior, só com as mudanças do Fei Long.
- backup/ssf2xjr1-chicken-wing.zip: só com o Chicken Wing.
- backup/ssf2xjr1.zip: original, sem mudanças.

## Validação da entrega

A rotina de reconhecimento foi executada em emulação 68000 isolada com Unicorn, comparando a ROM anterior com a nova, nas estruturas de memória de P1 e P2.
O Super sai com:
- a sequência completa;
- a sequência curta;
- a diagonal segurada enquanto o chute é apertado;
- 3 frames por direção.
O Super não sai com:
- um meia-lua só;
- a segunda diagonal faltando;
- nenhum botão no final;
- chute no lugar do soco;
- demora maior que a janela original entre as direções.
No cancelamento, o Super sai quando o chute médio acerta e não sai quando o golpe erra.
A ROM final foi descriptografada novamente e corresponde exatamente ao binário alterado. Só sfxj.03c mudou (16 bytes cifrados).
AINDA NÃO TESTADO: uma partida real no Fightcade.

PATCH: não há mais patches por mudança. A versão completa fica em patches/ (ex.: patches/v0.1/) e é aplicada sobre a sua própria ROM com: python tools/build_rom.py <ssf2xjr1.zip original> <saida.zip>
Detalhes e hashes: verification.json.
