# ADR-0001: Metodologia de patch na ROM CPS2 (ssf2xjr1)

Status: Aceito
Data: 2026-10-14 (retroativo, baseado no trabalho já feito em Chicken Wing)

## Contexto

A ROM `ssf2xjr1.zip` contém arquivos cifrados pelo encoder do CPS2 (ex.: `sfxj.04a`), que carrega o código 68000 do jogo. Qualquer alteração de comportamento (comandos, dano, timing) exige editar bytes dentro desse binário cifrado, sem quebrar a verificação de integridade do hardware/emulador e sem afetar outras rotinas.

## Decisão

- Usar a ferramenta [mbdcps2](https://github.com/MBDesu/mbdcps2) (v2.1.1) para descriptografar/recriptografar os arquivos do CPS2 dentro do ZIP.
- Fazer a engenharia reversa das rotinas em 68000 a partir do binário descriptografado (disassembly manual, guardado em `work/*.asm`), identificando as tabelas de reconhecimento de comando e as rotinas de movimento especial por personagem.
- Validar cada mudança de reconhecimento de comando com emulação 68000 isolada via Unicorn (`work/test_command.py`, `work/command-tests.json`), comparando a execução original vs. modificada com as estruturas de memória de P1 e P2, antes de reempacotar a ROM.
- Reempacotar com `work/package_rom.py`, gerar um `.ips` do arquivo interno alterado (não do ZIP) e descriptografar novamente o resultado final para confirmar que corresponde byte a byte ao binário pretendido.
- Documentar cada mudança em `characters/<personagem>/<new|old>/<nome-da-mudanca>/` com `LEIA-ME.txt` (instruções de teste em português) e `verification.json` (hashes e validação). O ZIP de teste fica só na máquina local (ignorado pelo git).
- Publicar as mudanças apenas como patches centrais por versão em `patches/<versão>/` (um `.ips` por arquivo interno alterado, com nome do projeto, mais um `manifest.json` com os hashes). O usuário monta a ROM a partir da própria cópia com `tools/build_rom.py`. Nenhum arquivo da Capcom é versionado (ver `.gitignore`).

## Consequências

- O CRC do arquivo interno alterado (ex.: `sfxj.04a`) muda; emuladores podem sinalizar divergência do conjunto original. Isso é esperado e documentado no LEIA-ME de cada entrega — a ROM é para teste local, não para redistribuição como "original".
- Cada mudança é isolada por personagem/rotina sempre que possível, para minimizar risco de efeitos colaterais em outras mecânicas.
- A validação automatizada (Unicorn) cobre reconhecimento de comando, mas não substitui teste manual em partida real (Fightcade/FBNeo) — isso é sempre listado como pendência explícita até ser feito.
