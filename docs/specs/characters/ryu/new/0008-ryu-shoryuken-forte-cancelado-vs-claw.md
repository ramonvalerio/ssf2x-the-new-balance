# Spec 0008: Ryu novo — Shoryuken forte em cancelamento conecta no Claw

Status: Entregue (v0.2) — pendente de confirmação no jogo
ADRs relacionados: `docs/adr/0007-principios-de-balanceamento.md` (princípio 2), `docs/adr/0006-leituras-de-dados-no-cps2.md`

## Problema

Ryu novo × Claw novo: soco forte em pé cancelado no Shoryuken forte. O Shoryuken não conectava em nenhuma das 6 tentativas da captura `work/logs/movements-20261014-050727.csv`.

## Diagnóstico

- O soco forte acerta o Claw a 36 px. O Shoryuken começa durante o hitstop do soco.
- A 1ª caixa de ataque do Shoryuken do Ryu (43) só fica ativa 4 frames depois do fim do hitstop. O Ken já tem caixa ativa nesse ponto.
- Nesses frames, o Claw escorrega com o recuo pesado do soco forte (curva 2) e chega a 74 px.
- A caixa 43 (`x=-30, rx=28`) alcança as caixas de "atingido" do Claw (id 5, recuadas: `+5/+35/+17`) só até **65 px**. Erro de ~9 px.
- Simulação com as posições capturadas: com o Claw parado na distância do soco forte, as caixas 43 e 44 acertam do 1º ao 7º frame ativo.

## Comportamento novo

O ajuste só acontece com **todas** estas condições ao mesmo tempo:
- o Ryu novo cancela um golpe normal (`$3 = $0A`) no Shoryuken forte (`$88 = 4`, `$9B = 4`);
- o oponente é o Claw novo;
- o Claw está em estado de "atingido" (`$3 = $0E`) e **ainda no hitstop** (`$47 ≠ 0`), antes de começar a escorregar.

Nesse caso, a curva de recuo pendente do Claw (`$11A`) passa a ser a curva 6 (4, 4, 4, 3…, 39 px), a mesma usada na Spec 0006. Ele fica a ~59–64 px quando o Shoryuken fica ativo, dentro do alcance de 65 px.

O soco forte em si não muda: fora do cancelamento no Shoryuken forte, o recuo continua o original.

## O que não muda

- Soco forte fora do cancelamento.
- Shoryuken fraco e médio, Hadouken e outros especiais.
- Shoryuken sem cancelamento.
- Claw antigo e os demais adversários.
- Claw defendendo.
- Caixas, dano e alcance.

## Implementação

- `0x7fb7e` (início dos especiais do Ryu novo): `move.b #$C,$3(a6)` → `jsr $8df28`. A instrução original é executada no fim do hook.
- Checagens em `0x8df28`, `0x8e08c` e `0x91ec8`. Esse espaço foi liberado convertendo os helpers de timer `0x8df18`, `0x8e07c` e `0x91eb8` para a rotina compartilhada `g`, com os mesmos valores.
- A curva 6 fica na tabela de dados em `0x792d4` (ROM crua).
- Script: `work/ryu_dp_vs_claw.py`. Testes (emulação fiel ao CPS2): `work/test_ryu_dp_vs_claw.py`, `work/ryu-dp-claw-tests.json`.

## Como testar no jogo

1. Monte a v0.2 com `python tools/build_rom.py <ssf2xjr1.zip original> <saida.zip>`. Ela já está instalada no Fightcade local.
2. Ryu novo × Claw novo: soco forte em pé cancelado no Shoryuken forte, dos dois lados e fora do canto. O Shoryuken deve acertar.
3. Compare com Shoryuken forte sem cancelamento e com soco forte isolado: devem continuar como antes.

## Validação

- Emulação fiel ao CPS2: a troca de curva só acontece no caso exato. Nos outros 8 casos o resultado é idêntico ao original e à v0.1: Claw já escorregando, Shoryuken fraco, Hadouken, sem cancelamento, Claw antigo, Ken, Fei e Claw defendendo.
- Os 3 helpers de tempo convertidos dão os mesmos valores do original.
- A ROM criptografada descriptografa idêntica ao binário alterado. O ZIP gerado por `tools/build_rom.py` é idêntico ao testado.

## Pendências

- Confirmar no jogo. Também falta o canto de tela, onde quem recua é o atacante.
- Pelo princípio 2 do ADR-0007, fazer o levantamento do Ryu (soco forte → Shoryuken forte) contra os demais personagens. Os que tiverem o mesmo problema entram na mesma regra.
