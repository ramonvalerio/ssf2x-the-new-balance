"""Monta a ROM do SSF2X - The New Balance a partir da SUA ROM original (ssf2xjr1.zip, set do MAME/FBNeo).

Uso:  python tools/build_rom.py <ssf2xjr1.zip original> [saida.zip] [--version v0.1]

Nenhum arquivo da Capcom é distribuído com o projeto: os patches em patches/ contêm só as
diferenças. O script confere os hashes do original antes e do resultado depois.
"""
import argparse, copy, hashlib, json, sys, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def apply_ips(data, patch):
    assert patch[:5] == b'PATCH', 'arquivo IPS inválido'
    out, p = bytearray(data), 5
    while patch[p:p + 3] != b'EOF':
        off = int.from_bytes(patch[p:p + 3], 'big'); size = int.from_bytes(patch[p + 3:p + 5], 'big'); p += 5
        if size == 0:   # RLE
            run = int.from_bytes(patch[p:p + 2], 'big'); out[off:off + run] = patch[p + 2:p + 3] * run; p += 3
        else:
            out[off:off + size] = patch[p:p + size]; p += size
    return bytes(out)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('original'); ap.add_argument('output', nargs='?', default='ssf2xjr1.zip')
    ap.add_argument('--version', default=None)
    a = ap.parse_args()
    manifests = sorted((ROOT / 'patches').glob('*/manifest.json'))
    m_path = (ROOT / 'patches' / a.version / 'manifest.json') if a.version else manifests[-1]
    m = json.loads(m_path.read_text(encoding='utf-8'))
    src = zipfile.ZipFile(a.original)
    files = {n: src.read(n) for n in src.namelist()}
    for part in m['parts']:
        got = hashlib.sha256(files[part['file']]).hexdigest()
        if got != part['original_sha256']:
            sys.exit(f"{part['file']}: hash diferente do ssf2xjr1 original esperado ({got})")
        new = apply_ips(files[part['file']], (m_path.parent / part['patch']).read_bytes())
        if hashlib.sha256(new).hexdigest() != part['patched_sha256']:
            sys.exit(f"{part['file']}: resultado inesperado depois do patch")
        files[part['file']] = new
    if Path(a.output).resolve() == Path(a.original).resolve():
        sys.exit('escolha um arquivo de saída diferente do original')
    with zipfile.ZipFile(a.output, 'w', zipfile.ZIP_DEFLATED) as out:
        for info in src.infolist():
            out.writestr(copy.copy(info), files[info.filename])
    print(f"{m['name']} {m['version']} gerado em {a.output}")

if __name__ == '__main__':
    main()
