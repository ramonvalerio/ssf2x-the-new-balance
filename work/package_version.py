"""Gera patches/<versão>/ a partir de um ZIP criptografado já testado, confere com tools/build_rom.py
e instala no Fightcade local (com cópia em backup/).

Uso: python work/package_version.py <versão> <zip testado> <versão anterior> "<item para o manifest>" [...]
"""
import hashlib, json, shutil, subprocess, sys, zipfile
from pathlib import Path

ver, tested, prev, *items = sys.argv[1:]
d = Path('patches') / ver
d.mkdir(parents=True, exist_ok=True)
v, n = zipfile.ZipFile('ssf2xjr1.zip'), zipfile.ZipFile(tested)

def ips(old, new):
    out = bytearray(b'PATCH'); i = 0
    while i < len(old):
        if old[i] == new[i]: i += 1; continue
        j = i
        while j < len(old) and j - i < 0xffff and (old[j] != new[j] or (j + 1 < len(old) and old[j + 1] != new[j + 1])): j += 1
        out += i.to_bytes(3, 'big') + (j - i).to_bytes(2, 'big') + new[i:j]; i = j
    return bytes(out + b'EOF')

changed = [x for x in v.namelist() if v.read(x) != n.read(x)]
assert changed == ['sfxj.03c', 'sfxj.04a'], changed
parts = []
for k, f in enumerate(changed, 1):
    name = f'ssf2x-the-new-balance-{ver}-part{k}.ips'
    (d / name).write_bytes(ips(v.read(f), n.read(f)))
    parts.append({'patch': name, 'file': f, 'original_sha256': hashlib.sha256(v.read(f)).hexdigest(),
                  'patched_sha256': hashlib.sha256(n.read(f)).hexdigest(), 'size': (d / name).stat().st_size})
m = json.loads((Path('patches') / prev / 'manifest.json').read_text(encoding='utf-8'))
m['version'] = ver; m['parts'] = parts; m['includes'] = items or m['includes']
(d / 'manifest.json').write_text(json.dumps(m, indent=2, ensure_ascii=False), encoding='utf-8')

out = Path(f'work/build-{ver}.zip')
subprocess.run([sys.executable, 'tools/build_rom.py', 'ssf2xjr1.zip', str(out), '--version', ver], check=True)
b = zipfile.ZipFile(out)
assert sorted(b.namelist()) == sorted(n.namelist()) and all(b.read(x) == n.read(x) for x in n.namelist()), 'build != testada'
shutil.copyfile(out, f'backup/ssf2xjr1-{ver}.zip')
shutil.copyfile(out, 'Fightcade/emulator/fbneo/ROMs/ssf2xjr1.zip')
print(ver, 'gerada, conferida e instalada:', hashlib.sha256(out.read_bytes()).hexdigest())
