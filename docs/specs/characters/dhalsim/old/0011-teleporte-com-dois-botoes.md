# Spec 0011: Dhalsim antigo — teleporte com os 3 botões em até 3 frames

Status: Entregue (v0.5) — pendente de confirmação no jogo. A v0.4 aceitava 2 dos 3 botões; foi substituída.

Mesma mudança da spec 0010 (`../new/0010-teleporte-com-dois-botoes.md`), aplicada ao Dhalsim antigo.

- A rotina de checagem dos botões do teleporte do Dhalsim antigo fica em `0x9f11e`. Ela é idêntica byte a byte à do novo (`0x8af1a`), e só o teleporte a usa (4 chamadas, em `0x9f034`–`0x9f060`).
- `0x9f11e` passa a desviar para `jmp $98542`, a mesma rotina compartilhada, que usa o mesmo histórico de botões por frame.
- Os mesmos 16 casos de teste da spec 0010 passaram no antigo (`work/dhalsim-teleport-tests.json`, entradas "antigo").
