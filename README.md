# SSF2X - The New Balance

Uma atualização de balanceamento competitivo de **Super Street Fighter II X** (CPS2, romset `ssf2xjr1`), para jogar no **FBNeo** / Fightcade.

> *A competitive rebalancing romhack of Super Street Fighter II X (Turbo) for the Final Burn Neo emulator.*

O SSF2X saiu em 1994 e nunca recebeu correções. Este projeto ajusta inconsistências e pontos de balanceamento com mudanças pequenas e documentadas, mantendo a identidade de cada personagem. Os critérios estão em [docs/adr/0007-principios-de-balanceamento.md](docs/adr/0007-principios-de-balanceamento.md).

## Aviso legal

Este repositório **não contém ROMs nem nenhum arquivo da Capcom**. Ele distribui só patches de diferenças, ferramentas e documentação. Para jogar, você precisa da sua própria cópia do romset `ssf2xjr1`. Super Street Fighter II X é marca e propriedade da Capcom. Este é um projeto de fã, sem fins lucrativos e sem ligação com a Capcom.

## Como jogar

1. Tenha o seu `ssf2xjr1.zip` original (set do MAME/FBNeo).
2. Monte a ROM do projeto (requer Python 3):
   ```
   python tools/build_rom.py caminho/para/ssf2xjr1.zip saida/ssf2xjr1.zip
   ```
   O script confere se a sua ROM é a original esperada, aplica os patches da versão mais recente e confere o resultado.
3. Coloque o ZIP gerado na pasta de ROMs do FBNeo com o nome `ssf2xjr1.zip` e abra o jogo. O emulador vai avisar que o CRC não bate com o original; isso é esperado.

A ROM modificada é para jogo local. Ela não é compatível com partidas online contra quem usa a ROM original.

## Mudanças (v0.1)

| Personagem | Mudança |
|---|---|
| Fei Long | Chicken Wing com comando em meia-lua (41236 + K) |
| Fei Long | Super liberado na janela do 2º Rekka (com barra cheia) |
| Ryu | Chute médio abaixado cancelável em Super durante todos os frames ativos |
| Ryu | Tatsu aéreo → Super em juggle (quantidade de hits depende da altura) |
| Ken | Shoryuken forte: 3º hit volta a acertar Ryu, Ken e Claw após o soco forte em pé |

Detalhes de cada mudança: `characters/<personagem>/README.md` e `docs/specs/`.

## Estrutura

| Pasta | Conteúdo |
|---|---|
| `patches/` | Patches por versão (`.ips` + `manifest.json` com hashes) |
| `tools/` | `build_rom.py`, que monta a ROM a partir da sua cópia |
| `characters/` | Documentação das mudanças por personagem (versões nova e antiga) |
| `fixes/` | Correções gerais |
| `docs/adr/` | Decisões técnicas e princípios do projeto |
| `docs/specs/` | Especificação de cada mudança de gameplay |
| `work/` | Scripts de engenharia reversa, patch e teste (emulação 68000 fiel ao CPS2), captura Lua e logs |

## Desenvolvimento

- **Ferramentas externas** (não incluídas, baixe separadamente): [mbdcps2](https://github.com/MBDesu/mbdcps2) para descriptografar e recriptografar o CPS2, além de `capstone` e `unicorn` para Python.
- **Processo:**
  1. capturar no jogo (`work/lua/capture-movements.lua`);
  2. diagnosticar;
  3. aplicar a mudança mínima;
  4. validar em emulação fiel ao CPS2 (`work/cps2emu.py`);
  5. testar no jogo.

  Veja `docs/adr/`.

## Licença

Código e documentação sob a licença [MIT](LICENSE). A licença não se aplica ao jogo original nem a nenhum material da Capcom.
