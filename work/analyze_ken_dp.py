"""Levantamento: soco forte em pé do Ken novo cancelado no Shoryuken forte.

Lê todas as capturas work/logs/movements-*.csv (script work/lua/capture-movements.lua),
detecta cada combo e gera work/logs/ken-dp-survey.md e .csv.
"""
import csv, glob, sys
from pathlib import Path

NAMES = ['Ryu', 'E. Honda', 'Blanka', 'Guile', 'Ken', 'Chun-Li', 'Zangief', 'Dhalsim',
         'M. Bison', 'Sagat', 'Balrog', 'Vega (Claw)', 'Cammy', 'T. Hawk', 'Fei Long', 'Dee Jay']
ST_HP_BOX = '5'                       # caixa de ataque do soco forte em pé (observado)
DP_BOXES = ['55', '43', '44']         # 1º, 2º e 3º hit do Shoryuken forte (observado)
KEN = '4'

def i(v):
    try: return int(v)
    except ValueError: return None

def combos(path):
    rows = list(csv.DictReader(open(path)))
    if not rows or 'p1_char' not in rows[0]:
        return []
    out, cur = [], None
    for n in range(1, len(rows)):
        r, p = rows[n], rows[n - 1]
        if r['p1_char'] != KEN or r['p1_old'] != '0':
            continue
        hit = i(r['p2_hp2a']) is not None and i(p['p2_hp2a']) is not None and i(r['p2_hp2a']) < i(p['p2_hp2a'])
        dist = abs(i(r['p2_x']) - i(r['p1_x']))
        if hit and r['p1_atkid'] == ST_HP_BOX and r['p1_st3'] == '10':
            if cur: out.append(cur)
            cur = {'file': Path(path).name, 'frame': n, 'char': i(r['p2_char']), 'old': r['p2_old'] == '1',
                   'dist_sthp': dist, 'hits': {}, 'dp_started': False, 'knockdown': False, 'end': None}
            continue
        if cur is None:
            continue
        if r['p1_st3'] == '12' and r['p1_mv88'] == '4':
            cur['dp_started'] = True
            if hit and r['p1_atkid'] in DP_BOXES:
                cur['hits'][r['p1_atkid']] = dist
            if r['p1_atkid'] == DP_BOXES[2] and 'gap3' not in cur:
                cur['gap3'] = dist           # distância no 1º frame ativo do 3º hit
        if r['p2_st3'] == '14' and i(r['p2_y']) and i(r['p2_y']) > 40 and r['p2_st5'] in ('2', '4'):
            cur['knockdown'] = True
        if cur['dp_started'] and r['p1_st3'] not in ('12',) and r['p2_st3'] != '14':
            out.append(cur); cur = None
    if cur: out.append(cur)
    return [c for c in out if c['dp_started']]

def main():
    files = sorted(glob.glob('work/logs/movements-*.csv'))
    all_c = [c for f in files for c in combos(f)]
    lines = ['# Ken novo: soco forte em pé → Shoryuken forte', '',
             f'Capturas lidas: {len(files)} · combos detectados: {len(all_c)}', '',
             '| Adversário | Versão | Arquivo | Dist. soco forte | 1º hit | 2º hit | 3º hit | Dist. no 3º hit ativo | Derrubou |',
             '|---|---|---|---|---|---|---|---|---|']
    for c in sorted(all_c, key=lambda c: (c['char'], c['old'], c['file'], c['frame'])):
        h = lambda k: f"✔ ({c['hits'][k]})" if k in c['hits'] else '✘'
        lines.append(f"| {NAMES[c['char']] if c['char'] is not None and c['char'] < 16 else c['char']} | {'antiga' if c['old'] else 'nova'} | "
                     f"{c['file']} | {c['dist_sthp']} | {h('55')} | {h('43')} | {h('44')} | {c.get('gap3', '—')} | {'sim' if c['knockdown'] else 'NÃO'} |")
    summary = {}
    for c in all_c:
        k = (NAMES[c['char']] if c['char'] is not None and c['char'] < 16 else str(c['char']), 'antiga' if c['old'] else 'nova')
        s = summary.setdefault(k, [0, 0]); s[0] += 1; s[1] += c['knockdown']
    lines += ['', '## Resumo por adversário', '', '| Adversário | Versão | Combos | Derrubou |', '|---|---|---|---|']
    for (name, ver), (n, kd) in sorted(summary.items()):
        lines.append(f'| {name} | {ver} | {n} | {kd}/{n} |')
    lines += ['', 'Entre parênteses: distância horizontal (px) no frame do acerto.']
    Path('work/logs/ken-dp-survey.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    with open('work/logs/ken-dp-survey.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['adversario', 'versao', 'arquivo', 'frame', 'dist_sthp', 'hit1', 'hit2', 'hit3', 'dist_hit3_ativo', 'derrubou'])
        for c in all_c:
            w.writerow([NAMES[c['char']] if c['char'] is not None and c['char'] < 16 else c['char'], 'antiga' if c['old'] else 'nova',
                        c['file'], c['frame'], c['dist_sthp'], c['hits'].get('55', ''), c['hits'].get('43', ''),
                        c['hits'].get('44', ''), c.get('gap3', ''), int(c['knockdown'])])
    print('\n'.join(lines))

if __name__ == '__main__':
    main()
