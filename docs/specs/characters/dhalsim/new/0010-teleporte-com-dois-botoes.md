# Spec 0010: Dhalsim novo — teleporte com 2 socos ou 2 chutes

Status: Entregue (v0.4) — pendente de confirmação no jogo
Mesma mudança no Dhalsim antigo: `../old/0011-teleporte-com-dois-botoes.md`

## Pedido

O teleporte deve exigir apertar 2 socos juntos em vez de 3. O original aceita 3 socos ou 3 chutes; a mudança vale para os dois.

## Diagnóstico

- O reconhecedor do teleporte do Dhalsim novo (`0x8ad44` → passos em `$88`) termina chamando `0x8af1a` com `d1 = $70` (socos) e depois `d1 = $700` (chutes).
- A rotina devolve Z=1 quando **todos** os botões da máscara foram apertados neste frame (`~$394 & $392`) ou **todos** foram soltos neste frame (negative edge).
- Só o teleporte chama essa rotina (4 chamadas, em `0x8ae30`–`0x8ae5c`).

## Comportamento novo

O teleporte sai quando **pelo menos 2** botões do mesmo tipo são apertados no mesmo frame (ou soltos no mesmo frame), além da direção, que não muda:
- 2 socos quaisquer (LP+MP, MP+HP, LP+HP) ou os 3;
- 2 chutes quaisquer ou os 3;
- vale também segurando um botão e apertando os outros dois juntos.

Continua **não** valendo: 1 botão só, soco com chute misturados, e segurar 2 e apertar o 3º.

## O que não muda

O comando direcional, os tempos entre as direções, para onde o Dhalsim vai (soco/chute e direção), a recuperação e os outros golpes.

## Implementação

- `0x8af1a` → `jmp $98542`. O endereço de retorno fica intacto e o chamador continua testando Z.
- A rotina nova fica em `0x98542`/`0x986ca` e é compartilhada com o Dhalsim antigo. Para cada máscara, testa `x & (x - 1) ≠ 0` (2 ou mais bits) sobre os botões apertados e depois sobre os soltos. Preserva `d1`, a máscara usada pelo chamador.
- Espaço: helpers de timer `0x98532` e `0x986ba` convertidos para a rotina compartilhada `g`, com os mesmos valores.
- Script: `work/dhalsim_teleport.py`. Testes (emulação fiel ao CPS2): `work/test_dhalsim_teleport.py`, `work/dhalsim-teleport-tests.json`.

## Como testar no jogo

1. Dhalsim novo: → ↓ ↘ ou ← ↓ ↙ + 2 socos juntos. Deve teleportar. Repita com 2 chutes e com os 3 botões.
2. Mesmo comando com 1 soco só: não teleporta (sai o golpe normal correspondente).
3. Atenção: um comando de teleporte com 2 botões, que antes saía como golpe normal, agora teleporta.

## Validação

- Emulação fiel ao CPS2: 16 combinações de botões, apertando e soltando, no Dhalsim novo e no antigo. O original só aceita os 3 botões. A versão nova aceita 2 ou 3 do mesmo tipo e rejeita 1 botão, soco com chute e "segurar 2 e apertar 1".
- Os 2 helpers convertidos dão os mesmos valores do original.
- A ROM gerada por `tools/build_rom.py` é idêntica à testada.
