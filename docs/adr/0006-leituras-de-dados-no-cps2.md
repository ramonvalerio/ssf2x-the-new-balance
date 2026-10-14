# ADR-0006: Leituras de dados no CPS2 e emulação de teste fiel

Status: Aceito (2026-10-14)
Data: 2026-10-14

## Contexto

O CPS2 descriptografa só os acessos ao espaço de programa: busca de instruções e operandos relativos ao PC, como `tabela(pc,d0.w)`. Qualquer outra leitura da ROM, por exemplo `(a0,d0.w)` depois de um `lea`, recebe os bytes **crus**, ainda criptografados.

Para liberar espaço (Specs 0002, 0004 e 0005), helpers de timer passaram a ler uma tabela aleatória compartilhada via `lea tabela(pc),a0` + `(a0,d0.w)`. No jogo real, isso devolveu bytes crus: timers de 0 a 255 frames em vez de 8 a 19. Os testes não pegaram o erro porque o Unicorn usava o binário descriptografado também para as leituras de dados.

Helpers afetados:
- **Fei Long:** `0x953dc`, `0x956b0`.
- **Ryu:** `0x7fd10`, `0x80014`, `0x7fb48`, `0x7fe72`.
- **Ken:** `0x852ce`, `0x85574`, `0x856ca`.

## Decisão

- **Tabelas lidas pelo jogo devem continuar com leitura relativa ao PC.** Quando um patch precisa reaproveitar uma tabela, usar uma rotina compartilhada `g` que faz `move.b tabela(pc,d0.w),d0` (em `0x8dc60`, tabela em `0x8dc6a`), chamada por `jsr`.
- **Os helpers do Sagat em `0x8dc5c` e `0x8ddb4` hospedam `g`.** Eles continuam fazendo o mesmo trabalho; `0x8dc5c` passa a desviar para `0x8ddc2`.
- **Todos os testes de agora em diante usam `work/cps2emu.py`.** Ele roda com o binário descriptografado e, nas leituras não relativas ao PC, entrega os bytes crus do ZIP gerado, como no hardware.

## Consequências

- Os valores dos timers voltam a ser idênticos aos do jogo original. Teste: 11 helpers × 32 índices, em `work/test_timers_cps2.py`.
- Espaço livre de verdade só vem de reorganizar código. Tabelas e áreas de `0x00`/`0xFF` na ROM crua estão em uso (gráficos, máscaras, tabelas).
- Os blocos de código das mudanças anteriores continuam nos mesmos endereços.
