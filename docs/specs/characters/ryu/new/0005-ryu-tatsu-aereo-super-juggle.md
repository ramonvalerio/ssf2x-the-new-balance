# Spec 0005: Ryu — Super acerta o adversário caindo depois do tatsu aéreo

Status: Entregue (versão 2) — `docs/specs/characters/ryu/new/0005-ryu-tatsu-aereo-super-juggle.md/` (v1 testada no jogo: funcionou com 1 hit; v2 pendente de teste)
ADR relacionado: `docs/adr/0005-caixa-de-vulnerabilidade-sintetica-para-juggle.md`

## Pedido

Quando o tatsu aéreo do Ryu acerta, o Super deve poder acertar o adversário antes de ele cair no chão, contando como combo.

## Dados capturados no jogo (antes da mudança)

Captura com `work/lua/capture-movements.lua` → `work/logs/air-tatsu.csv`:

- O tatsu aéreo usa caixa de ataque tipo `$1C`.
- Depois do acerto, o defensor fica com `$3 = $0E` (golpe), `$55 = $1C` e caixas de vulnerabilidade `0/0/0` durante toda a queda (~53 frames, do fim do hitstop até tocar o chão).
- O Ryu fica livre cerca de 6 frames depois de pousar e tem ~47 frames antes de o adversário cair.
- O projétil do Super usa tipo `$42` e aparece ~22 frames depois do comando.
- As flags de invulnerabilidade (`$1B3`, `$1A1`, `$1BF`) ficam em 0, e a regra de juggle (`0xbe708`) não restringe a reação `$1C`. O único bloqueio é a falta de caixa de vulnerabilidade.

## Comportamento novo

Na colisão com a 1ª caixa de vulnerabilidade do defensor (`0xbf558`), quando a animação dele não tem caixa, uma caixa sintética (id 1 da tabela de pernas do defensor) é usada se todas as condições abaixo valem:

- o ataque é do tipo `$42`;
- o defensor está em estado de golpe (`$3 = $0E`);
- a reação do defensor é `$1C`;
- o dono do projétil (`$26` do objeto) é o Ryu (`$391 = 0`).

## Versão 2 (2026-10-14): hits dependem da altura

Feedback do teste: funcionou, mas pegava só 1 hit. O pedido foi ter pelo menos 2 hits quando o Super acerta com o adversário quase no chão e 1 hit quando acerta alto, exigindo timing.

- **1º hit** (reação ainda `$1C`): só durante a queda (`$5 = 4`). Exclui o pouso (`$5 = 6`) e o quique (`$5 = 8`), observados na captura.
- **Hits seguintes** (a reação já mudou pelo hit do Super): só com o defensor no ar e baixo, `40 < y ≤ 64`. O chão fica em `y = 40` na captura, então o limite é 24 px acima do chão. O ajuste fica em `LOW_LIMIT`, no script.
- Sem caixa sintética para o defensor deitado no chão.
- Script: `work/ryu_air_tatsu_juggle2.py`. Testes: `work/ryu-air-tatsu-juggle2-tests.json`.

## O que não muda

Colisão com caixas reais, todos os outros ataques e personagens, regras de juggle, dano, barra.

## Riscos e pendências

- **Posição da caixa:** a caixa sintética usa a geometria de pé do defensor (pernas). É preciso confirmar no jogo que ela encontra o projétil durante a queda.
- **Reação `$1C` em outros golpes:** se outros golpes do Ryu derrubarem com a mesma reação `$1C`, o Super também os segue. Isso não foi verificado.
- **Arquivos:** `work/ryu_air_tatsu_juggle.py`, `work/ryu-air-tatsu-juggle-tests.json`.

## Como testar no jogo

1. Feche o emulador e abra pelo atalho "SSF2X (teste)". A ROM nova já está em Fightcade/emulator/fbneo/ROMs/ssf2xjr1.zip.
2. Com o Ryu novo e a barra cheia: tatsu aéreo acertando o adversário e, assim que pousar, ↓ ↘ → ↓ ↘ → + soco.
   Teste soltando o Super cedo (adversário alto: deve dar 1 hit) e mais tarde (adversário quase no chão: 2 hits ou mais).
3. Observe:
   - se o Super acerta o adversário caindo;
   - se o contador de combo sobe;
   - se o adversário cai e levanta normalmente depois.
4. Para comparar, faça um Super sem o tatsu antes e outros golpes no adversário caindo; tudo deve seguir como antes.
5. Se não funcionar, rode o script work/lua/capture-movements.lua durante o teste (como da outra vez) e me avise.

Backups:
- backup/ssf2xjr1-ryu-air-tatsu-juggle-1hit.zip: versão 1 desta entrega (sempre 1 hit).
- backup/ssf2xjr1-ryu-crmk-window.zip: versão anterior (Fei Long + chute médio abaixado do Ryu).
- backup/ssf2xjr1.zip: original.

## Validação da entrega

- A rotina de colisão das caixas do defensor foi executada em emulação 68000 isolada com Unicorn, comparando a ROM anterior com a nova.
- A caixa nova só aparece com o projétil do Super do Ryu e com o defensor caindo do knockdown $1C. Todos os casos com caixas reais, outros tipos de ataque, outros estados, outra reação e outro dono continuam idênticos.
- As tabelas de tempo unificadas (duas do Ryu e uma do Ken) produzem os mesmos valores.
- A ROM final foi descriptografada novamente e corresponde exatamente ao binário alterado. Mudaram sfxj.03c e sfxj.04a.
- AINDA NÃO TESTADO NO JOGO. Pontos incertos, que só o teste real confirma:
  - se a caixa das pernas fica na altura do projétil durante toda a queda;
  - como a animação de reação se comporta com o adversário no ar.
- Também não confirmei se outros golpes do Ryu (Shoryuken, por exemplo) derrubam com a mesma reação $1C. Se derrubarem, o Super também vai acertar depois deles.

PATCH: não há mais patches por mudança. A versão completa fica em patches/ (ex.: patches/v0.1/) e é aplicada sobre a sua própria ROM com: python tools/build_rom.py <ssf2xjr1.zip original> <saida.zip>
Detalhes e hashes: verification.json.
