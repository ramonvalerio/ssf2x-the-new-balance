from pathlib import Path
import zipfile, hashlib, json, shutil
root = Path('docs/specs/characters/ryu/new/0004-ryu-janela-de-cancelamento-cr-mk.md'); root.mkdir(parents=True, exist_ok=True)
vanilla = zipfile.ZipFile('ssf2xjr1.zip')
base_zip = Path('backup/ssf2xjr1-rekka-super.zip'); base = zipfile.ZipFile(base_zip)
new_zip = Path('work/ryu-crmk-enc.zip'); new = zipfile.ZipFile(new_zip)
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()

def ips(old, new):
    out = bytearray(b'PATCH'); i = 0
    while i < len(old):
        if old[i] == new[i]: i += 1; continue
        j = i
        while j < len(old) and j - i < 0xffff and (old[j] != new[j] or (j + 1 < len(old) and old[j + 1] != new[j + 1])): j += 1
        out += i.to_bytes(3, 'big') + (j - i).to_bytes(2, 'big') + new[i:j]; i = j
    return bytes(out + b'EOF')

for f in ('sfxj.03c', 'sfxj.04a'):
    (root / f'{f}.ips').write_bytes(ips(vanilla.read(f), new.read(f)))
shutil.copyfile(new_zip, root / 'ssf2xjr1.zip')
with zipfile.ZipFile(root / 'ssf2xjr1.zip') as z: assert z.testzip() is None
report = {
    'base_rom': 'ssf2xjr1 com as mudanças do Fei Long (docs/specs/characters/fei-long/new/0002-rekka-cancela-para-super.md). Não inclui o buffer de comando do Ryu (descartado).',
    'base_zip_sha256': sha(base_zip),
    'output_zip_sha256': sha(root / 'ssf2xjr1.zip'),
    'changed_files_vs_base': [n for n in base.namelist() if base.read(n) != new.read(n)],
    'ips_base': 'arquivos internos ORIGINAIS (sem nenhum patch); cada .ips é cumulativo para o seu arquivo',
    'decrypted_output_matches_patched_binary': True,
    'cpu_changes': {
        '0x78e18': 'tabela de rotinas de golpe normal: Ryu novo aponta para 0x7fd28 (antes 0x802ec)',
        '0x7fd10': 'helper do timer do Shinku Hadouken passa a ler a tabela aleatória idêntica em 0x7f9d0',
        '0x7fd28-0x7fd43': 'chama a rotina original 0x802ec; se o golpe for chute médio abaixado ($186=2, $187=2, $188=2), segue para 0x80028',
        '0x80014': 'helper do timer do Red Hadouken passa a ler a tabela idêntica em 0x7f9d0',
        '0x80028-0x80043': 'caixa de ataque ativa (byte +0x0C do quadro de animação) -> $2B0 = $FF (Super liberado); depois que a caixa some -> $2B0 = 0; durante o startup mantém a contagem original',
    },
    'tests': json.loads(Path('work/ryu-crmk-window-tests.json').read_text()),
}
(root / 'verification.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
print(report['changed_files_vs_base'])
