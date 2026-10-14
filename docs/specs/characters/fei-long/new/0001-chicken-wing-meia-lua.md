# Spec 0001: Chicken Wing do Fei Long — comando em meia-lua

Status: Entregue — `docs/specs/characters/fei-long/new/0001-chicken-wing-meia-lua.md/`

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
3. Copiar `docs/specs/characters/fei-long/new/0001-chicken-wing-meia-lua.md/ssf2xjr1.zip` para `Fightcade/emulator/fbneo/ROMs`, mantendo o nome.
4. Abrir `Fightcade/emulator/fbneo/fcadefbneo.exe`, carregar `ssf2xjr1`.
5. Selecionar Fei Long novo, testar 41236+K (fraco/médio/forte) dos dois lados. Restaurar com o ZIP de backup se necessário.

## Validação feita

Reconhecimento de comando validado em emulação 68000 isolada (Unicorn), original vs. modificado: meia-lua aceita, frente e quarto-de-lua rejeitados; estruturas de memória de P1 e P2 testadas. ROM final redescriptografada e conferida byte a byte contra o binário pretendido (apenas 2 bytes cifrados de `sfxj.04a` mudam).

## Pendente

Normalização de lado e teste em partida completa no Fightcade ainda não feitos.

## Como testar no jogo

1. Feche o emulador.
2. Faça uma cópia de segurança de Fightcade/emulator/fbneo/ROMs/ssf2xjr1.zip fora da pasta ROMs.
3. Copie o ssf2xjr1.zip desta pasta para Fightcade/emulator/fbneo/ROMs, mantendo esse nome.
4. Abra Fightcade/emulator/fbneo/fcadefbneo.exe e carregue ssf2xjr1 para teste local.
5. Selecione Fei Long novo e teste 41236 + chute fraco, médio e forte dos dois lados. Para restaurar, recoloque o ZIP de backup.

A alteração muda o CRC de sfxj.04a; o emulador pode informar divergência em relação ao conjunto original. Esta ROM é destinada a teste local.

## Validação da entrega

O reconhecimento do comando foi executado em emulação 68000 isolada com Unicorn, comparando original e modificado. Meia-lua aceita; frente e quarto de lua rejeitados; testadas as estruturas de memória de P1 e P2. A normalização do lado e uma partida completa no Fightcade ainda não foram testadas. As regras originais de acionamento e tempo dos botões foram preservadas.
A ROM final foi novamente descriptografada e corresponde exatamente ao binário alterado. Apenas dois bytes cifrados de sfxj.04a mudaram; os demais arquivos são idênticos.

PATCH: não há mais patches por mudança. A versão completa fica em patches/ (ex.: patches/v0.1/) e é aplicada sobre a sua própria ROM com: python tools/build_rom.py <ssf2xjr1.zip original> <saida.zip>
Detalhes e hashes: verification.json.
Ferramenta CPS2: https://github.com/MBDesu/mbdcps2 (v2.1.1).
