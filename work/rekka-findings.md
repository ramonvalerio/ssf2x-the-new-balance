# Achados: rotina de janela de input do Rekka Ken (Fei Long)

Data: 2026-10-14
Objetivo: localizar (não implementar) as checagens de janela de input pós-1º e pós-2º golpe do Rekka Ken, conforme ADR-0002 / Spec-0002.

## Metodologia usada

1. Parti das pistas em `Fightcade/.../ssf2xjr1.lua` e `character_specific.lua`, que já expõem endereços de RAM de trabalho ligados ao Rekka:
   - `rb(0xFF84DE)` → label "Rekka"
   - `rb(0xFF84EE)` → label "Rekka 2"
   - `rb(0xFF84FE)` → label "Rekka Sinken"
2. Em `character_specific.lua` (bloco `character_specific.feilong.specials`), os `memory_map` confirmam offsets de struct do personagem:
   - "Rekka": offsets `0x90` e `0xA0` (tamanho 4 cada)
   - "Rekka 2" (entrada comentada/incompleta no lua): offset `0xA0`
   - "Rekka Sinken": offset `0xB0` (tamanho `0x0A`, ou seja cobre $B0–$B9)
3. Os três endereços absolutos de RAM, subtraindo o respectivo offset, batem exatamente no mesmo endereço base:
   - `0xFF84DE - 0x90 = 0xFF844E`
   - `0xFF84EE - 0xA0 = 0xFF844E`
   - `0xFF84FE - 0xB0 = 0xFF844E`

   Isso confirma que `0xFF844E` é o endereço base da struct do personagem (P1) na RAM, equivalente ao registrador `a6` usado no código 68000 (o mesmo `a6` já visto em `work/fei-special.asm` para offsets como `$47(a6)`, `$4(a6)`, etc.). Ou seja: RAM 0xFF84DE = `$90(a6)`, RAM 0xFF84EE = `$A0(a6)`, RAM 0xFF84FE = `$B0(a6)`.
4. Com os offsets `$90`, `$A0/$A1/$A2/$A3` e `$AF/$B0` identificados, procurei no disassembly já existente em `work/fei-special.asm` os trechos que leem/escrevem esses offsets. Os trechos relevantes **já estavam presentes** no arquivo (não precisei adicionar disassembly novo); o trabalho foi identificar qual bloco corresponde a qual fase da corrente.

## Achados

### Bloco candidato à janela de aceitação do Rekka (transições 1º→2º e 2º→3º golpe)

Endereço: **`0x096bd4` até `0x096d34`** em `work/fei-special.asm` (arquivo já contém o disassembly byte a byte).

- Usa `$AF(a6)` como índice de estado (fase da corrente) e `$B0(a6)` como **contador de frames decrescente** — este é, com alta confiança, o "timer da janela de input".
- Em `0x096c72`, ao reconhecer a direção correta (`$3a6(a6)` = buffer de input, teste `andi #$2 / #$1`), o código recarrega `$B0(a6)` com o valor `0x0E` (14 frames) — a recarga explícita do timer da janela.
- Os blocos em `0x096c0a`, `0x096c20`, `0x096c34`, `0x096c46`, `0x096c5e`, `0x096c6e`, `0x096c8a` fazem, em sequência: decremento de `$B0(a6)`; se chegar a zero → `beq` para `0x096c46`, que faz `clr.b $AF(a6)` (zera o estado, ou seja a janela estourou / corrente perdida) e `rts`.
- Em `0x096c78`/`0x096c90` há checagem de botão via `jsr $44d0.w` e `jsr $44de.w` (rotinas de detecção de "botão pressionado", já usadas em outros pontos do arquivo para socos/chutes) — isso é a checagem do comando do próximo golpe do Rekka dentro da janela.
- Em caso de sucesso, `$AF(a6)` avança (`addq.b #$2, $AF(a6)`) para o próximo estado da tabela de salto em `0x096bea` (tabela de 7 entradas, compatível com duas transições de corrente: dir-check + botão-check para 1º→2º, e novamente para 2º→3º).
- Ao final da corrente (estado terminal, por volta de `0x096d0c`), o código zera `$AF(a6)`, `$90(a6)` (via `clr.b $4(a6)` / `clr.b $5(a6)`) e chama `jsr $5b60.w` — uma rotina comum de finalização/transição (possivelmente o disparo do projétil do Rekka ou entrada no estado de recovery), e **não há outro `addq`/recarga de `$B0(a6)` depois disso**.

### Confiança sobre qual trecho é "pós-1º" vs "pós-2º"

**Média.** Tenho certeza razoável de que:
- O contador `$B0(a6)` / offset `0xB0` é o timer da janela de input entre golpes do Rekka (mapeamento de RAM confirmado via lua + aritmética de offsets).
- A tabela de 7 estados em `$AF(a6)` cobre as duas transições da corrente (1º→2º e 2º→3º), repetindo o padrão "espera direção → espera botão → recarrega timer" duas vezes.

**Não tenho certeza absoluta** de qual par exato de estados (`$AF` = 0/2 vs 4/6 vs 8/10) corresponde à transição pós-1º-golpe e qual corresponde à pós-2º-golpe — isso exigiria rodar o jogo com breakpoint/logging no valor de `$AF(a6)` (ex.: via Unicorn, seguindo a metodologia de `work/test_command.py`) no momento exato em que o 1º e depois o 2º golpe conectam, e observar a sequência de valores. Não fiz essa validação dinâmica nesta fase (a tarefa pediu só localização, não implementação/validação).

### Checagem pós-3º golpe

**Não encontrei evidência de uma janela equivalente depois do 3º golpe.** A tabela de estados em `$AF(a6)` tem 7 entradas, suficiente para 2 transições (não 3), e o estado terminal (~`0x096d0c`) limpa os contadores e sai da lógica de corrente, chamando uma rotina de finalização em vez de recarregar o timer de novo. Isso é consistente com a suposição do ADR-0002 ("provavelmente não [há janela pós-3º]"), mas também não é 100% certo — não tracei para onde `jsr $5b60.w` leva nem confirmei se ele reabre algum outro tipo de janela por caminho indireto.

### Bloco relacionado: `$90(a6)` (RAM 0xFF84DE, "Rekka")

Endereço: **`0x096b96` até `0x096c08`**. Este bloco usa `$90(a6)` como índice de estado de nível superior (dispatcher), que decide se o personagem está na animação/estado de Rekka e delega para o bloco `$AF/$B0` acima via jump table em `0x096bba`. Confiança alta de que isso é o "estado da ação Rekka" que engloba a máquina de estados da corrente, mas não é, por si, a checagem de janela — é o dispatcher que a contém.

### Bloco `$A0(a6)` (RAM 0xFF84EE, "Rekka 2") — candidato alternativo, não confirmado

Endereço: **`0x0963d8` até `0x0964d2`**. Também é uma máquina de estados com contador decrescente (`$A1(a6)`) e checagem de direção (`$3a6(a6)` AND `0xF` comparado a `4` e `6`, ou seja D-pad back/forward) seguida de checagem de botão via `$44d0`/`$44de`, e recarrega o timer ao avançar de estado. Estruturalmente é **muito parecido** com o bloco `$AF/$B0` acima.

Isso levanta uma possibilidade que não consegui descartar com os recursos desta fase: **pode ser que `$A0/$A1` e `$AF/$B0` sejam duas rotinas distintas para fases diferentes da corrente** (ex.: `$A0/$A1` = janela pós-1º-Rekka, `$A1/$B0` = janela pós-2º-Rekka), em vez de uma única máquina de 7 estados cobrindo as duas transições como assumi acima. As duas hipóteses são compatíveis com as evidências estáticas que levantei; **diferenciá-las exige instrumentação dinâmica** (rodar o jogo/ROM e logar quando cada bloco é executado, correlacionando com qual golpe do Rekka acabou de conectar).

## Resumo da incerteza (seja explícito, como pedido)

- **Certo (alta confiança):** endereço base da struct do personagem = `0xFF844E` (P1) = `a6`; offsets `$90`, `$A0`, `$AF/$B0` confirmados por aritmética de RAM + memory_map do lua.
- **Razoavelmente certo (confiança média):** os blocos `0x096bd4–0x096d34` (timer `$B0`) e/ou `0x0963d8–0x0964d2` (timer `$A1`) implementam as janelas de input entre golpes do Rekka, com recarga de timer, checagem de direção e checagem de botão.
- **Incerto, não resolvido:** qual desses dois blocos (ou qual par de estados dentro de um único bloco de 7 estados) corresponde exatamente à transição pós-1º-golpe vs pós-2º-golpe. Recomendo resolver isso com um teste dinâmico (breakpoint/log no valor de `$AF(a6)` e `$A0(a6)` via emulação Unicorn ou via o próprio FBNeo com Lua, observando o exato frame em que o 1º e o 2º golpe do Rekka conectam) antes de decidir onde inserir a checagem do Super do Spec-0002.
- **Não encontrado / não confirmado:** uma janela de input explícita depois do 3º golpe. A estrutura de estados sugere que não existe, mas não é uma confirmação definitiva (não segui o destino de `jsr $5b60.w`).

## Arquivos relevantes

- `work/fei-special.asm` — já contém o disassembly dos blocos citados (endereços `0x096bb2–0x096d34` e `0x0963d8–0x0964d2`); não precisei adicionar nada novo, pois o disassembly já cobria essas rotinas (o arquivo não é só sobre Chicken Wing).
- `Fightcade/emulator/fbneo/fbneo-training-mode/games/ssf2xjr1/character_specific.lua` (linhas ~826–880) — memory_map usado para derivar os offsets de struct.
- `Fightcade/emulator/fbneo/fbneo-training-mode/games/ssf2xjr1/ssf2xjr1.lua` (linhas ~1030–1036, ~1175–1180) — endereços absolutos de RAM usados para a derivação.
- `docs/adr/0002-janela-do-segundo-rekka-aceita-super.md` e `docs/specs/0002-rekka-cancela-para-super.md` — contexto/objetivo final (não implementado).

## Próximo passo sugerido (fora do escopo desta tarefa)

Antes de implementar o Spec-0002, validar dinamicamente (Unicorn ou FBNeo+Lua com breakpoint de memória em `0xFF844E+$AF` e `0xFF844E+$A0`) qual bloco/estado é acionado exatamente após o 2º golpe conectar, para confirmar o ponto exato de inserção da checagem de Super antes de modificar a ROM.
