# Spec 0020: Guile — 2º soco fraco abaixado encadeado cancela em Flash Kick (pausado)

Status: Pausado — mecanismo da janela de cancelamento identificado, ponto de início do 2º hit ainda não localizado
ADR relacionado: nenhum ainda (feature nova)

## Pedido

Soco fraco abaixado do Guile já cancela em Flash Kick quando é o único hit (confirmado pelo usuário, comportamento original). Quando encadeado (soco fraco, soco fraco), o 2º hit não cancela. Pedido: o 2º hit também deve poder cancelar (tanto faz ser o 1º ou o 2º a cancelar), mas depois do 2º hit não pode mais cancelar nada. Sem mudar nenhum comportamento original — só acrescentar essa opção.

Comparação dada pelo usuário: o soco médio abaixado do Guile já cancela em Flash Kick (comportamento original, mesma mecânica que o 1º soco fraco) — serve de referência para o que "cancelável" deve parecer.

## O que foi confirmado (captura + execução ao vivo)

Scripts: `work/lua/capture-movements.lua` (campos `spc195`=`$195`, `m186`/`m187`/`m188`=`$186`/`$187`/`$188`, todos offsets do atacante) e `work/lua/probe_guile_cancel.lua` (contador de execução por endereço via `memory.registerexec`, que funciona neste build — diferente do caso do Blanka, aqui a ferramenta deu resultados claros).

- Campo-chave: `$195(a6)` ("special_cancel" em `memory_addresses.lua`). Fica não-zero durante os quadros ativos do golpe quando o cancelamento está liberado; checagem de corte é `tst.b $392(a6)` XOR `$394(a6)` (input atual vs anterior) mascarado por bit, em `0x8497c`/`0x84a30` (bits `$10` e `$100`, provavelmente dois grupos de botão diferentes).
- Rotina que abre a janela: `0x7f018`. Lê o personagem (`$391`), escolhe entre duas tabelas de valores iniciais (`$195`, `$2B0`) em `0x7f04c`, grava em `$195(a6)` e (num dos dois caminhos) também em `$2B0(a6)`.
- Único chamador confirmado ao vivo: `0x7b38e` (`jmp $7f018.l`), dentro de um bloco que também zera `$280`/`$2be`, grava `$18b=1` (attack_flag) — bloco de "começo de golpe normal, estado 10" em `0x7b350`-`0x7b394`.
- **Confirmado com `registerexec` em 3 capturas separadas, sempre o mesmo padrão:** no 1º soco fraco abaixado, `0x7f018`/`0x7b38e` disparam (contador sobe) e `$195` fica não-zero (6, decaindo). No 2º soco fraco encadeado, **nem `0x7f018` nem `0x7b38e` disparam** (contador trava) e `$195` fica 0 o tempo todo — é exatamente isso que impede o cancelamento.
- Também descartado: `$2B0(a6)` não é o que libera o encadeamento em si (ele também cai pra 0 e fica 0 durante o 2º hit, mas o 2º hit acontece mesmo assim — ou seja, o encadeamento golpe-a-golpe não depende de `$2B0` nem de `$195`).

## O que foi tentado e não achou o ponto exato

Localizei a árvore de despacho do Guile por personagem (idx=3 nas tabelas em `0x78e18` e `0x7b2ae`, formato confirmado batendo com a Spec 0004 do Ryu: idx=0 é `0x802ec`, igual citado na spec dele):

- `0x83bec` → `0x842c8`: dispatcher de "qual botão foi apertado" por `$186`/`$187`/`$188`. **Nunca disparou** nas capturas, nem durante o 1º hit — a precondição (`jsr $448a; bgt.w`) não foi satisfeita nos testes feitos, ou esse caminho não é o usado aqui.
- `0x8432c`–`0x84496`: blocos que decidem "o próximo normal encadeado" por distância (`0x843b8`) e marcam `$8e(a6)`/`$8f(a6)` = 1 quando o encadeamento é aceito (ex.: `0x84354`, `0x84390`). **Testados com `registerexec` e nunca dispararam**, nem uma vez, durante uma sequência onde o encadeamento claramente aconteceu (2º soco saiu). Hipótese descartada.
- `0x844b0`/`0x8492c`/`0x84970`: handler por quadro do golpe ativo (roda todo quadro, inclusive durante o 2º hit) — não é um gatilho pontual, só o "tick" genérico; não ajudou a isolar o momento exato da transição.

Conclusão: o 2º hit claramente reinicia a animação/hitbox (volta pro mesmo `atkid`), mas **não passa pelo pipeline "começo de golpe novo"** (`0x83bec`/`0x842c8`/`0x7b38e`/`0x7f018`) nem pelos blocos de "confirma encadeamento" já testados. O ponto real ainda não foi localizado.

## Por que parou aqui

A técnica de `memory.registerexec` funciona bem neste caso (ao contrário da investigação do Blanka) e já reduziu bastante o espaço de busca, mas localizar o ponto exato exige mais rodadas de captura direcionada. Parado por pedido do usuário após uma investigação já mais longa que o normal, sem ter achado o ponto com confiança suficiente pra propor um patch cirúrgico.

## Próximos passos (quando retomar)

- Instrumentar escritas (`memory.registerwrite`, que dá endereço+tamanho+valor, confirmado funcionando) no campo de animação do atacante (`$1A`, ponteiro de quadro) e no próprio `atkid` (via a função `attack_box` do script de captura) pra pegar o exato quadro em que o 2º hit começa, e then testar `registerexec` em endereços mais próximos dali (ex.: dentro do handler por quadro `0x844b0`/`0x8492c`/`0x84970`, que já se sabe que roda nesse momento — faltou granularidade: só testei a entrada desses blocos, não os pontos internos onde `$4(a6)`/`$3(a6)` seriam escritos).
- Considerar que o encadeamento pode ser decidido inteiramente dentro do handler por quadro já instrumentado (`0x844b0` em diante), sem nunca sair dele — ou seja, sem passar pelos dispatchers "começo de golpe" a que associamos erroneamente a 0x83bec/0x842c8. Vale mapear TODAS as escritas em `$3(a6)`/`$4(a6)` dentro desse bloco com `registerwrite`.
- Depois de achar o ponto, o padrão de correção é o mesmo da Spec 0004 do Ryu: chamar `0x7f018` (ou replicar seu efeito) também nesse ponto, só quando for a 2ª vez consecutiva do mesmo golpe (soco fraco abaixado) do Guile — não mexer em mais nada, pra não derrubar a trava "depois do 2º hit não cancela mais" que o usuário pediu.

## Scripts/arquivos desta investigação

- `work/lua/capture-movements.lua` (campos `spc195`, `m186`, `m187`, `m188` acrescentados)
- `work/lua/probe_guile_cancel.lua` (contador de execução + campos de memória combinados por quadro)
- `work/logs/guile-cancel-exec-probe.csv`, `work/logs/guile-cancel-combined.csv`
- `work/logs/movements-20261015-014728.csv` (captura original: 1 hit cancela, 2 hits não)
