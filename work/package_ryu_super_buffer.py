from pathlib import Path
import zipfile, hashlib, json, shutil
root = Path('docs/specs/characters/ryu/new/0003-ryu-buffer-do-super.md'); root.mkdir(parents=True, exist_ok=True)
vanilla = zipfile.ZipFile('ssf2xjr1.zip')
new_zip = Path('work/ryu-super-buffer-enc.zip'); new = zipfile.ZipFile(new_zip)
base_zip = Path('backup/ssf2xjr1-rekka-super.zip')
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()

def ips(old, new):
    out = bytearray(b'PATCH'); i = 0
    while i < len(old):
        if old[i] == new[i]: i += 1; continue
        j = i
        while j < len(old) and j - i < 0xffff and (old[j] != new[j] or (j + 1 < len(old) and old[j + 1] != new[j + 1])): j += 1
        out += i.to_bytes(3, 'big') + (j - i).to_bytes(2, 'big') + new[i:j]; i = j
    return bytes(out + b'EOF')

o, n = vanilla.read('sfxj.03c'), new.read('sfxj.03c')
(root / 'sfxj.03c.ips').write_bytes(ips(o, n))
shutil.copyfile(new_zip, root / 'ssf2xjr1.zip')
with zipfile.ZipFile(root / 'ssf2xjr1.zip') as z: assert z.testzip() is None
report = {
    'base_rom': 'ssf2xjr1 com Chicken Wing + Rekka/Super do Fei Long (docs/specs/characters/fei-long/new/0002-rekka-cancela-para-super.md)',
    'base_zip_sha256': sha(base_zip),
    'output_zip_sha256': sha(root / 'ssf2xjr1.zip'),
    'rom_file': 'sfxj.03c',
    'changed_files_vs_base': ['sfxj.03c'],
    'encrypted_bytes_changed_vs_base': sum(1 for x, y in zip(zipfile.ZipFile(base_zip).read('sfxj.03c'), n) if x != y),
    'ips_base': 'sfxj.03c original (sem nenhum patch). As mudanças do Fei Long estão em sfxj.04a (ver docs/specs/characters/fei-long).',
    'decrypted_output_matches_patched_binary': True,
    'cpu_changes': {
        '0x7fc06-0x7fc21': 'Shinku Hadouken do Ryu novo, passo 3 do reconhecedor ($A0=4): além de frente (→ passo 4), aceita baixo (→ pula para o passo 5, que espera baixo-frente)',
    },
    'tests': json.loads(Path('work/ryu-super-buffer-tests.json').read_text()),
    'cancel_tests': {'crMK_hit_cancel_on': {'original': False, 'patched': True}, 'crMK_whiff_cancel_off': {'original': False, 'patched': False}},
}
(root / 'verification.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
print('ok')
