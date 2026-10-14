# Specs: mudanças de gameplay

Cada arquivo descreve **uma** mudança: o problema, o diagnóstico, o comportamento novo, o que fica preservado, a implementação, como testar no jogo e a validação. Ao lado de cada spec fica o `NNNN-….verification.json`, com hashes e resultados de teste.

Decisões técnicas e princípios (como e por que mudar) ficam em `docs/adr/`. O critério para aceitar uma mudança está em `docs/adr/0007-principios-de-balanceamento.md`.

## Organização

```
docs/specs/
  characters/<personagem>/
    README.md      tabela das mudanças do personagem
    new/           specs da versão Super (nova)
    old/           specs da versão antiga
  global/          specs de mudanças globais do jogo
```

A numeração `NNNN` é única no projeto inteiro e nunca é reaproveitada. Status possíveis: `Proposto`, `Em andamento`, `Entregue (vX.Y)`, `Descartado`. As mudanças entregues entram nos patches de `patches/<versão>/`.
