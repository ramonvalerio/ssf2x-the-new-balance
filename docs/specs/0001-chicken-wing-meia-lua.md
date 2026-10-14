# Spec 0001: Chicken Wing do Fei Long — comando em meia-lua

Status: Entregue — `characters/fei-long/new/chicken-wing-half-circle/`

## Personagem / golpe

Fei Long (versão **nova** apenas — não se aplica ao Fei Long antigo). Chicken Wing.

## Comando

Olhando para a direita: trás, baixo-trás, baixo, baixo-frente, frente + chute (41236 + K). Inverte ao olhar para a esquerda.

Substitui apenas a exigência final (era cima-frente, passa a ser frente). As tolerâncias, tempos e demais etapas do comando original são preservados.

## O que não muda

Dano, propriedades de hit, startup/recovery, e o comando do Fei Long antigo.

## Como testar

1. Fechar o emulador.
2. Backup de `Fightcade/emulator/fbneo/ROMs/ssf2xjr1.zip` fora da pasta `ROMs`.
3. Copiar `characters/fei-long/new/chicken-wing-half-circle/ssf2xjr1.zip` para `Fightcade/emulator/fbneo/ROMs`, mantendo o nome.
4. Abrir `Fightcade/emulator/fbneo/fcadefbneo.exe`, carregar `ssf2xjr1`.
5. Selecionar Fei Long novo, testar 41236+K (fraco/médio/forte) dos dois lados. Restaurar com o ZIP de backup se necessário.

## Validação feita

Reconhecimento de comando validado em emulação 68000 isolada (Unicorn), original vs. modificado: meia-lua aceita, frente e quarto-de-lua rejeitados; estruturas de memória de P1 e P2 testadas. ROM final redescriptografada e conferida byte a byte contra o binário pretendido (apenas 2 bytes cifrados de `sfxj.04a` mudam).

## Pendente

Normalização de lado e teste em partida completa no Fightcade ainda não feitos.
