# Patches

Cada versão do **SSF2X - The New Balance** fica em `patches/<versão>/`:

- `ssf2x-the-new-balance-<versão>-partN.ips`: só as diferenças, uma parte por arquivo interno do romset que foi alterado.
- `manifest.json`: qual parte vale para qual arquivo interno e os hashes SHA-256 esperados antes e depois.

Não há nenhuma ROM nem arquivo da Capcom neste repositório. Você precisa da sua própria cópia do romset **ssf2xjr1** (Super Street Fighter II X, Japão, rev 1, set do MAME/FBNeo).

## Como montar a ROM

```
python tools/build_rom.py caminho/para/ssf2xjr1.zip saida/ssf2xjr1.zip
```

- Sem `--version`, usa a versão mais recente. Com `--version v0.1`, usa a versão escolhida.
- O script confere se a sua ROM é a original esperada, aplica os patches e confere o resultado.
- Copie o ZIP gerado para a pasta de ROMs do FBNeo com o nome `ssf2xjr1.zip`. O emulador vai avisar que o CRC não bate com o original; isso é esperado.

Por que dois arquivos? No CPS2, um patch IPS vale para um único arquivo interno do romset. As mudanças ficam em `sfxj.03c` e `sfxj.04a`, por isso cada versão tem uma parte para cada um. O script aplica as duas juntas.

## Versões

| Versão | Conteúdo |
|---|---|
| v0.1 | Fei Long (Chicken Wing em meia-lua; Super na janela do 2º Rekka). Ryu (janela do chute médio abaixado para Super; tatsu aéreo → Super em juggle). Ken (Shoryuken forte com 2º hit de recuo menor contra Ryu, Ken e Claw). Correção dos timers de comando. |
| v0.2 | v0.1 + Ryu: soco forte em pé → Shoryuken forte conecta no Claw (spec 0008). |
| v0.3 | v0.2 + global: janela de 6 frames para reversal no levantar (spec 0009). |
| v0.4 | v0.3 com a janela de reversal reduzida para 4 frames + Dhalsim (novo e antigo): teleporte com 2 socos ou 2 chutes (specs 0010/0011). |
| v0.5 | v0.4 com o teleporte do Dhalsim voltando a exigir os 3 botões, agora aceitos em até 3 frames (specs 0010/0011). |
| v0.6 | v0.5 + Akuma: teleporte com os 3 botões em até 3 frames (spec 0012). |
| v0.7 | v0.6 + Ryu: soco forte (em pé e abaixado) cancelável em Super durante os frames ativos, mesma regra do chute médio abaixado (spec 0014). |
| v0.8 | v0.7 + Fei Long: Flame Kick liberado na janela após o segundo Rekka (spec 0015). |
| v0.9 | v0.8 + Ken: 2º hit do Shoryuken forte cancela no Super com a barra cheia (spec 0017). |
