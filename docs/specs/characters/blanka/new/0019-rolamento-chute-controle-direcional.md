# Spec 0019: Blanka — controle direcional no rolamento com chute (pausado)

Status: Pausado — diagnóstico incompleto, nenhuma alteração na ROM
ADR relacionado: nenhum ainda (feature nova, não uma correção de inconsistência do ADR-0007)

## Pedido

Rolamento com chute (trás-carga, frente + chute fraco/médio/forte): no hit confirm, se o jogador segurar **frente**, o Blanka atravessa o adversário e continua (como já acontece hoje só com o chute fraco, perto do adversário); se segurar **trás** (ou neutro), mantém o comportamento original de recuar — isso para qualquer força de chute, não só o fraco.

## O que foi confirmado por captura (jogo real)

Script: `work/lua/capture-movements.lua` (campos `input` = `$392`, `facing` = `$12`, `phase4` = `$4`, `timer3e` = `$3E`, todos no objeto do atacante, offsets em `memory_addresses.lua`).

- Com **chute fraco**, perto do adversário: segurando `input=1` (frente, considerando `facing=1`) o Blanka atravessa; segurando `input=2` (trás) ele volta. O jogo já lê o direcional durante esse golpe específico.
- Com **chute médio/forte**: no teste padrão (sem segurar direção, `input=0`) ele sempre volta — igual ao que acontece com o fraco segurando trás.
- **Importante (aviso do usuário):** o comportamento original do chute fraco também depende da distância — mesmo sem mexer no direcional, perto ele atravessa e longe ele pode voltar. Isso não foi isolado do efeito do direcional nos testes feitos.
- `facing` ($12) fica constante (não é o Blanka virando de lado que causa o "voltar").
- `timer3e` ($3E) decai ao longo do golpe e, no momento em que o Blanka volta, o valor é reiniciado para um número positivo nesse exato frame — confirma que existe um timer interno controlando fases do golpe, mas o ponto exato do código que faz essa escolha **não foi localizado com confiança**.

## O que foi tentado e não funcionou

1. **Desmontagem estática** (Capstone sobre `work/ssf2xjr1-decrypted.bin`): localizei um despachante de fases por `$4(a6)` em `0x81ad0`, com um bloco (`0x81b60`–`0x81c70`) que parecia certo (checagem de força do chute via `$15(a6)` com 3 ramos, setup de `$3c/$3e/$40/$42`). **Essa hipótese estava errada** — confirmado depois que o endereço nunca executa durante o golpe de verdade.
2. **Patch cirúrgico nessa hipótese** (`work/blanka_roll_direction.py`, hooks em `0x80eb2`/`0x811fe`, ponto de troca em `0x81bae`): validado em emulação isolada (Unicorn) com todos os casos de direção/lado/timer corretos, mas **não teve efeito no jogo real** — o código patchado nunca é alcançado. ROM revertida (`backup/ssf2xjr1-antes-roll-direction.zip`).
3. **Varredura ampla de padrões similares** (chute fraco/médio/forte com setup de velocidade) em todo o ROM: 28 candidatos, depois 22 — nenhum executa durante o golpe (confirmado com `memory.registerexec`, que funciona neste build — testado contra o hook da Spec 0001, que disparou corretamente).
4. **Leitura de registradores da CPU pelo Lua**: `memory.getregister("pc")`, `"a7"`, `"sp"`, `"a6"` — todos retornam `nil` neste build do FBNeo. Não dá pra ler o PC nem o topo da pilha (o que serviria pra achar quem chama uma rotina compartilhada conhecida).
5. **Busca por constante exata gravada em `$3E`** (ex.: `move.w #$900,$3e(a6)`, o valor de reinício observado numa captura): achei ocorrências em outros pontos do ROM, mas o contexto ao redor não bate com o golpe do Blanka (é uma estrutura de 2 ramos, não os 3 ramos de força de chute esperados — provavelmente golpe de outro personagem).

## Causa real ainda não isolada

A hipótese mais provável continua sendo um timer interno (`$3E` ou equivalente) que decai com o tempo e cujo sinal decide recuar ou não no hit confirm — e que o jogo já consulta o direcional (`$392`) em algum ponto próximo a esse timer, pelo menos para o chute fraco. Falta achar o endereço de código real que faz essa leitura, para então condicionar a checagem de direção a qualquer força de chute.

## Por que parou aqui

Sem acesso ao PC/registradores pelo Lua neste build do FBNeo, e com a desmontagem estática já tendo levado a pelo menos uma hipótese errada (testada e revertida), continuar por tentativa e erro arrisca mais patches sem efeito. Acompanhar o ADR-0007 princípio 4 (diagnóstico antes de alterar) significa não aplicar mudança nenhuma até achar o ponto certo com confiança.

## Próximos passos (quando retomar)

- Um depurador/emulador com acesso real a registradores e breakpoints de execução (ex.: rodar a ROM crua num 68k debugger separado, ou um build do FBNeo com suporte a `memory.getregister`) resolveria a limitação do item 4 diretamente.
- Alternativa: capturar um savestate do FBNeo no meio do golpe e tentar carregar seu estado de RAM num emulador Unicorn controlado (como `work/cps2emu.py` já faz para leitura de dados crus), o que daria rastreamento de PC completo sem depender da API Lua. Não tentado ainda nesta spec — exigiria entender o formato de savestate do FBNeo.
- Isolar o efeito da distância do efeito do direcional no chute fraco antes de generalizar a regra para médio/forte (observação do usuário, ainda não testada separadamente).

## Scripts/arquivos desta investigação

- `work/lua/capture-movements.lua` (campos `input`, `facing`, `phase4`, `timer3e` acrescentados)
- `work/lua/probe_blanka_roll.lua`, `work/lua/probe_exec_sanity.lua`, `work/lua/probe_write_args.lua`, `work/lua/probe_caller.lua`, `work/lua/probe_api2.lua` (sondas de API/execução)
- `work/blanka_roll_direction.py` (patch cirúrgico, validado em emulação, **não aplicado na ROM final** — revertido)
- `work/logs/blanka-roll-exec-probe.csv`, `work/logs/blanka-roll-pc-trace.csv`, `work/emutest/out/caller_probe.txt`, `work/emutest/out/write_args.txt`
