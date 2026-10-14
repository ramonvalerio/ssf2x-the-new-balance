# Spec 0010: Dhalsim novo — teleporte com os 3 botões em até 3 frames

Status: Entregue (v0.5) — pendente de confirmação no jogo. A v0.4 aceitava 2 dos 3 botões; foi substituída a pedido do usuário.
Mesma mudança no Dhalsim antigo: `../old/0011-teleporte-com-dois-botoes.md`

## Pedido

Manter os 3 socos (ou 3 chutes) do original, mas sem exigir que caiam exatamente no mesmo frame, para aumentar a chance de acerto.

## Diagnóstico

- O reconhecedor do teleporte do Dhalsim novo (`0x8ad44` → passos em `$88`) termina chamando `0x8af1a` com `d1 = $70` (socos) e depois `d1 = $700` (chutes).
- A rotina devolve Z=1 quando **todos** os botões da máscara foram apertados **neste mesmo frame** (`~$394 & $392`), ou todos soltos neste frame (negative edge).
- A leitura é feita 60 vezes por segundo. Os 3 dedos precisam cair dentro de ~16 ms, e a margem real é menor e aleatória. Só o teleporte chama essa rotina.

## Comportamento novo

- Os 3 botões do mesmo tipo continuam obrigatórios, mas podem ser apertados ao longo de até **3 frames** seguidos: o 2º e o 3º até 2 frames depois do 1º, cerca de 50 ms.
- Soltar os 3 juntos (negative edge) continua valendo como no original, no mesmo frame.
- Continua **não** valendo:
  - só 2 botões ou 1 botão;
  - soco com chute misturados;
  - botões apertados há mais de 3 frames.

## O que não muda

O comando direcional, os tempos entre as direções, para onde o Dhalsim vai, a recuperação e os outros golpes.

## Implementação

- **Histórico de botões (global):** no hook de início de frame (`0x782a0` → `0x93f3a`, compartilhado com a spec 0009), o jogo guarda os botões recém-apertados num byte empacotado (bits 0–2 socos, 4–6 chutes):
  - `$3EA` = este frame;
  - `$3EB` = 1 frame antes;
  - `$3F1` = 2 frames antes.

  São bytes que o jogo não usa. O hook continua fazendo o trabalho original e a contagem do reversal; a continuação dele fica em `0x98828`.
- **Checagem:** `0x8af1a` → `jmp $98542`. A rotina compartilhada testa se `$3EA | $3EB | $3F1` contém todos os bits da máscara. Se não contém, faz a checagem original de soltar. Preserva `d1` e o retorno em Z, como o chamador espera.
- **Espaço:** helpers de timer `0x98532`, `0x986ba` e `0x98818` convertidos para a rotina compartilhada `g`, com os mesmos valores.
- **Arquivos:** script em `work/dhalsim_teleport.py`; testes (emulação fiel ao CPS2, frame a frame) em `work/test_dhalsim_teleport.py` e `work/dhalsim-teleport-tests.json`.

## Como testar no jogo

1. Dhalsim novo: → ↓ ↘ ou ← ↓ ↙ + os 3 socos "juntos", sem precisar de precisão perfeita. Deve teleportar. Repita com os 3 chutes.
2. Com só 2 socos: não teleporta.
3. Apertando os botões bem espaçados (mais de ~3 frames): não teleporta.

## Validação

- **Emulação fiel ao CPS2:** sequências frame a frame passando pelo hook de início de frame, no Dhalsim novo e no antigo (16 casos cada):

  | Situação | Original | Nova |
  |---|---|---|
  | 3 botões no mesmo frame | sai | sai |
  | 3 botões em 2 ou 3 frames | não sai | sai |
  | 3 botões em 4 frames | não sai | não sai |
  | Só 2 botões, 1 botão, soco com chute misturados | não sai | não sai |
  | Soltar os 3 juntos | sai | sai |
  | Soltar os 3 espalhados | não sai | não sai |

- **Hook de início de frame:** mantém os efeitos originais e a contagem do reversal.
- **Helpers:** os 3 convertidos dão os mesmos valores do original.
- **ROM:** a gerada por `tools/build_rom.py` é idêntica à testada.
