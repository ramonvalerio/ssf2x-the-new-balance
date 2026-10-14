# ADR-0007: Princípios de balanceamento do projeto

Status: Aceito (2026-10-14)
Data: 2026-10-14

## Contexto

O SSF2X é de 1994 e nunca recebeu correções, porque arcade não tinha patch. Parte do que hoje parece "característica" ficou no jogo só porque não havia como ajustar depois. Este projeto é uma atualização de balanceamento. Por isso, "é assim no original" não basta como justificativa para manter algo, e "é diferente do original" também não basta como motivo para mudar.

O caso que motivou este ADR: no combo soco forte em pé → Shoryuken forte do Ken, o número de hits e a derrubada variavam conforme o adversário (Spec 0006). Isso acontecia por diferenças de pixels nas caixas de "atingido" e pelo recuo, e não por uma regra escrita no jogo. A rotina de colisão é a mesma para todos e não consulta o personagem.

## Decisão: princípios

### 1. Preservar a identidade dos personagens
Ficam como no original, salvo decisão explícita de balanceamento:
- tamanho, postura e caixas de vulnerabilidade **no neutro** (em pé, agachado, pulando, andando);
- alcance, velocidade e prioridade dos golpes;
- quem passa por cima de quê, quem é mais fácil ou mais difícil de acertar.

Essas diferenças definem como cada personagem joga e como funcionam os confrontos.

### 2. Corrigir inconsistências de combo
Quando um combo é executado do mesmo jeito, o resultado deve ser o mesmo contra qualquer adversário:
- **Golpes especiais de vários hits devem conectar todos os hits** quando o primeiro hit entra em combo, a uma distância de combo normal (por exemplo, normal cancelado em especial).
- **Golpes que derrubam devem derrubar** em todos os adversários nessas mesmas condições.
- Uma diferença que depende só de detalhes de caixa, invisíveis para o jogador, durante um combo já confirmado é tratada como inconsistência, não como traço de personagem.

### 3. Mudanças cirúrgicas
- Cada mudança é limitada ao caso exato: atacante, golpe, hit e, quando necessário, defensor. Rotinas e tabelas compartilhadas não são alteradas.
- Quem já se comporta de acordo com estes princípios fica idêntico ao original.
- Entre as soluções possíveis, escolher a que altera menos. Exemplo: reduzir o recuo de um hit em vez de aumentar o alcance do golpe, porque mudar o alcance afetaria o neutro.

### 4. Diagnóstico antes de alterar
- Capturar no jogo (`work/lua/capture-movements.lua`), medir e entender a causa antes de propor a mudança.
- Validar com simulação ou emulação fiel ao CPS2 (`work/cps2emu.py`, ADR-0006) e confirmar no jogo.
- Para pares de personagens, fazer um levantamento (ex.: `work/analyze_ken_dp.py`) e aplicar a mesma regra a todos os casos encontrados, não só ao primeiro relatado.

### 5. Entrada sem sorte de frame
Nenhuma regra depende de dois botões caírem no **mesmo frame** de leitura (60 por segundo). Quando um comando exige vários botões, ele aceita os botões apertados dentro de uma janela de 3 frames. Quando um comando exige timing (por exemplo, reversal ao levantar), a janela é a que um jogador experiente consegue no original com piano e negative edge, mas com um único toque.
- Aplicado em: reversal ao levantar (Spec 0009), teleporte do Dhalsim novo e antigo (Specs 0010/0011) e do Akuma (Spec 0012). Uma varredura do código encontrou só esses três pontos com exigência de botões simultâneos.
- O mesmo vale para o código de seleção do Akuma (3 socos no mesmo frame, em `0xe960`).

### 6. Exceções
- Situações de canto de tela, distância máxima, trocas simultâneas e outros casos-limite são avaliados separadamente. Não entram automaticamente no princípio 2.
- Qualquer desvio destes princípios precisa de um ADR ou de uma spec própria explicando o motivo.

## Aplicação imediata (proposta)

Shoryuken forte do Ken, combo soco forte em pé → Shoryuken forte:
- **Derrubada:** já corrigida contra Ryu, Ken e Claw (Spec 0006).
- **Pendente pelo princípio 2:** o 1º hit erra no Claw (a ~36 px). Pelo princípio, ele deve conectar.
- **Antes de corrigir:** completar o levantamento com os demais personagens (versões nova e antiga) e corrigir todos os casos de uma vez, com a mesma regra.

## Consequências

- Decisões futuras passam a ter um critério escrito. O objetivo é um jogo mais justo e previsível em combos, sem perder as diferenças de personagem no neutro.
- Os princípios podem gerar uma lista grande de correções. Cada uma segue o processo do princípio 4.
- Se a revisão mudar algum princípio, este ADR é atualizado (ou substituído) antes de novas mudanças de gameplay.
