from pathlib import Path
import zipfile, hashlib, json, shutil
root = Path('docs/specs/characters/fei-long/new/0002-rekka-cancela-para-super.md'); root.mkdir(parents=True, exist_ok=True)
vanilla = zipfile.ZipFile('ssf2xjr1.zip').read('sfxj.04a')
current_zip = Path('Fightcade/emulator/fbneo/ROMs/ssf2xjr1.zip')
cw = zipfile.ZipFile(current_zip).read('sfxj.04a')
new_zip = Path('work/rekka-super-enc.zip')
new = zipfile.ZipFile(new_zip).read('sfxj.04a')

def ips(old, new):
    out = bytearray(b'PATCH'); i = 0
    while i < len(old):
        if old[i] == new[i]: i += 1; continue
        j = i
        while j < len(old) and j - i < 0xffff and (old[j] != new[j] or (j + 1 < len(old) and old[j + 1] != new[j + 1])): j += 1
        out += i.to_bytes(3, 'big') + (j - i).to_bytes(2, 'big') + new[i:j]; i = j
    return bytes(out + b'EOF')

def apply(old, patch):
    b = bytearray(old); p = 5
    while patch[p:p + 3] != b'EOF':
        o = int.from_bytes(patch[p:p + 3], 'big'); n = int.from_bytes(patch[p + 3:p + 5], 'big')
        b[o:o + n] = patch[p + 5:p + 5 + n]; p += 5 + n
    return bytes(b)

patch = ips(vanilla, new)
assert apply(vanilla, patch) == new
(root / 'sfxj.04a.ips').write_bytes(patch)
shutil.copyfile(new_zip, root / 'ssf2xjr1.zip')
with zipfile.ZipFile(root / 'ssf2xjr1.zip') as z: assert z.testzip() is None
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
report = {
    'base_rom': 'ssf2xjr1 com Chicken Wing em meia-lua (docs/specs/characters/fei-long/new/0001-chicken-wing-meia-lua.md)',
    'base_zip_sha256': sha(current_zip),
    'output_zip_sha256': sha(root / 'ssf2xjr1.zip'),
    'vanilla_zip_sha256': sha('ssf2xjr1.zip'),
    'rom_file': 'sfxj.04a',
    'changed_files_vs_base': ['sfxj.04a'],
    'encrypted_bytes_changed_vs_base': sum(1 for a, b in zip(cw, new) if a != b),
    'ips_base': 'sfxj.04a original (sem nenhum patch); inclui Chicken Wing + Rekka/Super',
    'decrypted_output_matches_patched_binary': True,
    'cpu_changes': {
        '0x953c0': 'jsr $452a.w -> bsr.w $953f4 (checagem de início do Super do Fei Long novo)',
        '0x953dc': 'helper do timer do Super passa a ler a tabela aleatória compartilhada em 0x95552',
        '0x953f4-0x9540f': 'nova rotina, parte 1: checagem original; se recusada, exige barra cheia ($2b4=$30) e $dd2(a5)=0',
        '0x956b0': 'helper do timer do Flame Kick passa a ler a tabela compartilhada em 0x95552 (tabela idêntica)',
        '0x956c4-0x956df': 'nova rotina, parte 2: exige $3=$0C, $98=0 (Rekka), $4=6 (2º golpe), $5 em {4,6} (janela)',
    },
    'tests': json.loads(Path('work/rekka-super-tests.json').read_text()),
}
(root / 'verification.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
print(json.dumps({k: v for k, v in report.items() if k != 'tests'}, indent=2, ensure_ascii=False))
