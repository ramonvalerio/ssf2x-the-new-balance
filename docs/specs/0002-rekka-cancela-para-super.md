# Spec 0002: Rekka Ken do Fei Long — cancelar para Super na janela do 2º golpe

Status: Entregue — `characters/fei-long/new/rekka-super/` (pendente: teste em partida real no Fightcade)
ADR relacionado: `docs/adr/0002-janela-do-segundo-rekka-aceita-super.md`

## Personagem / golpe

Fei Long. Rekka Ken (sequência de até 3 golpes encadeados).

## Comportamento atual

- Após o 1º Rekka: janela própria aceita o comando do 2º Rekka.
- Após o 2º Rekka: janela própria aceita o comando do 3º Rekka.
- Essas janelas não aceitam nada além do respectivo próximo Rekka.

## Comportamento desejado

Durante a janela que segue o **2º Rekka** (a mesma janela que hoje só aceita o 3º golpe):

- Se o jogador inserir o comando normal do Super do Fei Long **e** a barra de super estiver cheia, a sequência é desviada para o Super em vez de continuar para o 3º Rekka. A barra é consumida normalmente, como em qualquer acionamento do Super.
- Se o jogador inserir o comando do 3º Rekka (sem o Super), o comportamento é o atual, inalterado.
- Se a barra não estiver cheia, o comando do Super dentro dessa janela é ignorado e a janela continua funcionando apenas como hoje (aceitando o 3º Rekka).
- Se nada for inserido, a janela estoura normalmente como hoje.

## O que não muda

- Janela após o 1º Rekka: comportamento atual, sem aceitar Super.
- Janela após o 3º Rekka (se existir alguma checagem pós-3º golpe): inalterada.
- Comando, dano, tolerâncias e timing do 1º e do 3º Rekka.
- Comando, dano e propriedades do Super do Fei Long fora desse contexto (uso normal do Super continua igual).

## Pontos de atenção para a implementação

- O comando do Super não deve ser ambíguo com o comando do 3º Rekka — precisa ficar claro, ao olhar a tabela de inputs em `work/fei-special.asm`, que os dois buffers de comando não se sobrepõem de um jeito que dispare o errado.
- A checagem de barra cheia precisa ocorrer antes de confirmar o desvio para o Super (não só checar o input).
- Confirmar em qual endereço/rotina fica essa janela de 2º→3º golpe (ainda não localizada no disassembly atual — `work/fei-special.asm` e `work/fei.asm` cobrem principalmente Chicken Wing; Rekka ainda não foi mapeado).

## Como testar (quando implementado)

1. Fechar o emulador e fazer backup do ZIP da ROM atual.
2. Copiar a ROM modificada para `Fightcade/emulator/fbneo/ROMs/ssf2xjr1.zip`.
3. Com a barra cheia, executar 1º Rekka, 2º Rekka, e então o comando do Super durante a janela seguinte — confirmar que o Super sai e a barra é consumida.
4. Repetir sem a barra cheia — confirmar que o comando do Super é ignorado e a janela ainda aceita o 3º Rekka normalmente.
5. Repetir o fluxo normal (1º, 2º, 3º Rekka sem Super) dos dois lados — confirmar que nada mudou.

## Validação planejada

Seguir a mesma metodologia do ADR-0001: reconhecimento de comando validado em emulação 68000 isolada (Unicorn) antes de reempacotar, depois teste manual em FBNeo/Fightcade.

## Implementação (2026-10-14)

- O reconhecedor do Super (`$B0/$B1`) já roda a cada frame, inclusive durante o Rekka (`0x782a6` → `0x95118`), antes da rotina de ação. Ele era barrado pela checagem genérica `$452a`, que recusa quando `$3 == $0C` (personagem já em golpe especial).
- Em `0x953c0`, `jsr $452a` foi trocado por `bsr` para uma rotina nova. Ela roda a checagem original e, se essa recusar, libera o Super quando todas as condições abaixo valem:
  - `$3 = $0C` (em golpe especial);
  - `$98 = 0` (o golpe é o Rekka);
  - `$4 = 6` (2º golpe);
  - `$5` igual a 4 ou 6 (sub-estados em que o 3º Rekka é aceito);
  - `$2B4 = $30` (barra cheia);
  - `$DD2(a5) = 0` (jogo não pausado).
- Se liberado, segue o caminho normal de início do Super (`0x953d4`). A barra é consumida pela própria inicialização do Super.
- O espaço foi obtido unificando cópias idênticas da tabela aleatória de timer (Super e Flame Kick passam a ler a de `0x95552`).
- Diferença conhecida: o sub-estado 6 só aceita o 3º Rekka enquanto `$15 = 0`; o Super não faz essa checagem, então pode ser aceito alguns frames a mais no fim da animação.
- Script e testes: `work/rekka_super.py`, `work/rekka-super-tests.json`, `work/package_rekka_super.py`.
