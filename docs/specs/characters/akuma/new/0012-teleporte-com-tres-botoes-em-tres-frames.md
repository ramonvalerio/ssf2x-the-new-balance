# Spec 0012: Akuma — teleporte (Ashura Senku) com os 3 botões em até 3 frames

Status: Entregue (v0.6) — pendente de confirmação no jogo
Mesma regra do Dhalsim: `../../dhalsim/new/0010-teleporte-com-dois-botoes.md`

## Problema

O teleporte do Akuma exige os 3 socos (ou 3 chutes) **no mesmo frame de leitura**. É o mesmo problema do Dhalsim: com 60 leituras por segundo, dois dedos que caiam em frames vizinhos fazem o comando falhar, por sorte.

## Diagnóstico

A rotina que verifica os botões do teleporte do Akuma fica em `0xa7fc8`. Ela é idêntica byte a byte às do Dhalsim novo (`0x8af1a`) e antigo (`0x9f11e`), e só o reconhecedor do teleporte a chama (4 chamadas, `0xa7f56`–`0xa7f82`).

## Comportamento novo

Os 3 botões do mesmo tipo continuam obrigatórios, mas podem ser apertados em até 3 frames seguidos. Soltar os 3 no mesmo frame (negative edge) continua como no original. Direcional, tempos e recuperação não mudam.

## Implementação

`0xa7fc8` → `jmp $98542`, a rotina compartilhada da spec 0010, que usa o histórico global de botões por frame (`$3EA`, `$3EB`, `$3F1`). Os 16 casos de teste da spec 0010 passaram também para o Akuma (`work/dhalsim-teleport-tests.json`, entradas "akuma").

## Princípio

Esta é a terceira e última exigência de botões simultâneos no mesmo frame encontrada no jogo. Pelo ADR-0007 (princípio 6), nenhuma regra deve depender de dois dedos caírem no mesmo frame.
