# Spec 0006: Ken novo — Shoryuken forte acerta os 3 hits no Ryu, no Ken e no Claw

Status: Entregue — `characters/ken/new/shoryuken-hit2-pushback/` (pendente: teste no jogo)
ADR relacionado: `docs/adr/0006-leituras-de-dados-no-cps2.md` (forma de liberar espaço e testes)

## Problema

Soco forte em pé → Shoryuken forte: derruba o Fei Long com 4 hits, mas contra o Ryu (e o Claw) o 3º hit do Shoryuken não acerta e o adversário não cai.

## Diagnóstico

Capturas em `work/logs/movements-*.csv`, analisadas com `work/analyze_ken_dp.py`.

- Recuo no acerto: o byte `+8` da caixa de ataque vai para `$4C`, que vira `$1FD` (`0x7ad16`). Os substitutos `$2A1→$2A2` e `$2A3→$2A4` têm prioridade, e a curva é escolhida em `0x78fdc` a partir da tabela em `0x79250`, lida como dado (ROM crua).
- Curvas: 0 = 4,4,4,4,3… (30 px); 1 = 6,6,6,5… (54 px); 2 = 8,8,8,7… (78 px); 3 = sem recuo; 4 = 1,1,1… (12 px); 5 = 2,2,2… (20 px); 6 = 4,4,4,3,3… (39 px).
- O 2º hit (caixa 43) aplica a curva 2. A caixa do 3º hit (44) tem `x=-27, rx=26`: alcance de 53 px.
- As caixas de "atingido" do Ryu (ids 24/17/16) ficam recuadas: `+13/+33/+42`. No frame 153 da captura, a ponta do 3º hit estava em 763 e as pernas do Ryu começavam em 767: erro de 4 px.
- O Claw também tem caixas recuadas (e ainda perde o 1º hit). O Fei tem caixas para a frente.

## Comportamento novo

Só para o caso exato **Ken novo + Shoryuken (`$3=$0C`, `$88=4`) + quadro com caixa de ataque 43 + defensor Ryu ou Ken novo**, `$2A1 = 7`. Isso força a curva 6 (39 px). Versão 1: `$2A1 = 2` (curva 1), só contra o Ryu; substituída, ver abaixo.

## O que não muda

O 1º e o 3º hit, outros golpes e personagens, Ken e Ryu antigos, caixas, dano e defesa.

## Versão 2 (2026-10-14): curva 6, defensores Ryu e Ken

- Captura Ken × Ken (`movements-20261014-033225.csv`): mesmo problema (3º hit a 64–72 px).
- O simulador `work/ken_dp_reach.py` reaplica cada curva sobre os deslocamentos reais capturados, com espelhamento quando o Ken está à direita, e testa a sobreposição das caixas frame a frame. Resultados:
  - **Curva 2 (original):** erra em todos os combos, como no jogo.
  - **Curva 1:** acerta o Ryu por ~2 px e **erra** no Ken × Ken com o lado trocado.
  - **Curva 6:** acerta em todos os combos normais de Ryu, Ken e Claw, a ~52 px.
  - **Canto de tela:** nenhuma curva resolve, porque o recuo passa para o atacante e o simulador não modela isso.
- Mudança: defensor Ryu **ou** Ken novo (`andi.b #$fb` sobre o id) e `$2A1 = 7` (curva 6).

## Versão 3 (2026-10-14): Claw

- Ken × Ken confirmado no jogo pelo usuário.
- Claw (id 11): a simulação com as capturas mostra o 3º hit acertando com a curva 6 fora do canto (~52 px). O 1º hit continua errando no Claw (original).
- Checagem do defensor: `cmpi.b #11,d0` / `andi.b #$fb,d0`, que aceita só os ids 0, 4 e 11 da versão nova. O código passou para 4 blocos; o helper `0x8b5d8` também foi convertido para `g`.

## Implementação

- `0x7ad16`: `jsr $8aefa`. A instrução original é executada dentro do hook.
- Checagens em `0x8aefa`, `0x8b0ba`, `0x8b25a` e `0x8b5e8`. Esse espaço foi liberado convertendo os helpers de timer `0x8aeea`, `0x8b0aa`, `0x8b24a` e `0x8b5d8` para a rotina compartilhada `g`, com os mesmos valores.
- Script: `work/ken_dp_vs_ryu.py`. Testes (emulação fiel ao CPS2): `work/test_ken_dp_vs_ryu.py`, `work/ken-dp-ryu-tests.json`.

## Próximos passos

- Confirmar no jogo, de perto e na distância máxima.
- Claw e outros: completar o levantamento com `work/analyze_ken_dp.py` e, se necessário, acrescentar entradas no mesmo hook, como regra por defensor.
