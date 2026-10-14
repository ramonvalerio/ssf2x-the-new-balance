# Spec 0015: Fei Long — segundo Rekka cancela para Flame Kick

Status: Entregue (v0.8) — pendente de confirmação em partida real

## Comportamento

Durante a janela que segue o segundo Rekka, o Fei Long novo pode executar o Flame Kick com o comando original (trás, baixo, baixo-trás + chute). O jogador continua podendo completar o terceiro Rekka ou cancelar para o Super, conforme a spec 0002.

As três forças do Flame Kick são aceitas. O cancelamento não é liberado durante os frames ativos do segundo Rekka, depois do primeiro ou do terceiro Rekka, durante outro especial ou com o jogo pausado. O Flame Kick no neutro permanece inalterado.

## Implementação

O reconhecedor original do Flame Kick (`$94/$95`) continua processando direção, botão, força e tempo. Em `0x95682`, a checagem genérica de início de especial (`$4542`) passa por uma extensão que aceita também o caso exato:

- `$3 = $0C`: Fei Long está executando um especial;
- `$98 = 0`: o especial atual é o Rekka;
- `$4 = 6`: segundo Rekka;
- `$5` igual a 4 ou 6: janela em que o terceiro Rekka é aceito;
- `$DD2(a5) = 0`: jogo não está pausado.

Duas cópias idênticas da tabela aleatória de tempo foram redirecionadas para a cópia compartilhada em `0x95552`. Os espaços liberados em `0x964D6` e `0x989C8` guardam a checagem nova. Os helpers continuam produzindo exatamente os mesmos valores.

## Teste no jogo

1. Selecione o Fei Long novo.
2. Execute o primeiro e o segundo Rekka.
3. Durante a janela do terceiro Rekka, faça o comando original do Flame Kick com chute fraco, médio e forte.
4. Confirme que o Flame Kick sai dos dois lados da tela.
5. Confirme que o terceiro Rekka e o cancelamento para Super continuam funcionando.
6. Confirme que o Flame Kick não sai cedo, durante os frames ativos do segundo Rekka.

## Validação

A rotina foi validada em emulação Motorola 68000 isolada para P1 e P2. Os casos positivos foram os dois subestados da janela após o segundo Rekka, com LK, MK e HK. Os casos negativos cobriram os frames ativos do segundo Rekka, as janelas do primeiro e terceiro Rekka, outro especial e pausa. O acionamento no neutro e os timers permaneceram idênticos à v0.7.

A ROM recriptografada foi descriptografada novamente e corresponde exatamente ao binário modificado. Ainda falta confirmação visual em uma partida real no Fightcade.
