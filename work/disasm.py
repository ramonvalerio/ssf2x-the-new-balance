exec(open('work/scan_rom.py').read().split('print(b[:32]')[0])
print('table',b[0x95176:0x9517e].hex())
for i in c.disasm(b[0x9517e:0x952e0],0x9517e): print(f'{i.address:06x} {i.bytes.hex():20} {i.mnemonic:10} {i.op_str}')
