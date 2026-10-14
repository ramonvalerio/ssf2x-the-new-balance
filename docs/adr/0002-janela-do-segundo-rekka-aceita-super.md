# ADR-0002: Reaproveitar a janela do 2º Rekka para aceitar o Super (Fei Long)

Status: Aceito (implementado em 2026-10-14)
Data: 2026-10-14

## Contexto

O Rekka Ken do Fei Long é uma sequência de até três golpes encadeados. Depois do 1º Rekka, existe uma janela de input própria em que o jogo aceita o comando do 2º Rekka; depois do 2º, há outra janela própria que aceita o comando do 3º Rekka. Essas janelas são checagens de input independentes das checagens normais de special/super do restante do jogo.

Quer-se que, durante a janela de aceitação do 3º Rekka (a janela que segue o 2º golpe), o jogador também possa cancelar a sequência para o Super do Fei Long, gastando a barra, em vez de ser obrigado a continuar a corrente ou deixar a janela estourar.

## Decisão

- Modificar apenas a checagem de input associada à janela **após o 2º Rekka**. As janelas após o 1º e após o 3º golpe continuam com o comportamento atual, inalterado.
- Dentro dessa janela, antes de (ou junto com) a checagem existente do comando do 3º Rekka, adicionar uma checagem do comando normal do Super do Fei Long (o mesmo input que já aciona o Super fora da corrente), condicionada à barra de super estar cheia.
- Se o Super for reconhecido e a barra estiver cheia, a sequência é desviada para a rotina do Super em vez de para o 3º Rekka. Se não, a checagem original do 3º Rekka segue valendo normalmente.
- Nenhuma alteração nas tolerâncias de timing da janela, no dano, nas propriedades de hit ou no reconhecimento do 1º/3º Rekka.

## Alternativas descartadas

- **Super cancelável em qualquer um dos dois primeiros golpes**: rejeitado por ora — o pedido é especificamente a janela do 2º golpe (a que já existe para aceitar o 3º). Pode ser um ADR futuro se o jogador quiser estender.
- **Criar uma janela de input nova e separada para o Super**, paralela à janela do 3º Rekka: mais arriscado (duas janelas concorrentes lendo o buffer de input ao mesmo tempo) e desnecessário, já que a janela do 3º Rekka já faz exatamente a leitura de buffer necessária.

## Consequências

- Risco principal: a checagem de barra cheia e a checagem de comando do Super precisam ser lidas sem corromper o estado que a checagem do 3º Rekka também usa (mesmo buffer de input, possivelmente mesmos registradores/flags). Exige inspecionar a rotina da janela do 2º→3º Rekka em `work/fei-special.asm` antes de decidir o ponto exato do desvio.
- Precisa validar que o jogador não pode "roubar" o Super sem barra cheia nem acidentalmente cancelar para Super ao tentar emendar o 3º Rekka normalmente (ambiguidade de input: o comando do Super não deve colidir com o comando do 3º Rekka).
- Ver especificação funcional detalhada em `docs/specs/0002-rekka-cancela-para-super.md`.
