"""Simula o 3º hit do Shoryuken forte do Ken com cada curva de recuo no 2º hit, usando uma captura."""
import csv, sys
sys.path.insert(0, 'work')
from cps2emu import raw_program
raw = raw_program('ssf2xjr1.zip')
def l(a): return int.from_bytes(raw[a:a+4], 'big')
def w(a): return int.from_bytes(raw[a:a+2], 'big', signed=True)
def sb(a): v = raw[a]; return v - 256 if v > 127 else v
def hb(c, old): return l(0x10026c + 4 * (c + (0x11 if old else 0)))
def atk(c, i):
    t = hb(c, 0) + w(hb(c, 0) + 6); a = t + i * 16
    return sb(a), sb(a + 1), raw[a + 2], raw[a + 3]
def vul(c, old, slot, i):
    if i == 0: return None
    t = hb(c, old) + w(hb(c, old) + slot); a = t + i * 4
    return sb(a), sb(a + 1), raw[a + 2], raw[a + 3]
def curve(n):
    base = 0x79250; a = base + w(base + 2 * n); out = []
    while raw[a] < 0x80: out.append(raw[a]); a += 1
    return out

def overlap(kx, ky, box, dx, dy, vboxes):
    ax, ay, arx, ary = box
    cx, cy = kx - ax, ky + ay          # Ken faces right: offsets are negated (forward = +x)
    for vb in vboxes:
        if vb is None: continue
        vx, vy, vrx, vry = vb
        ex, ey = dx + vx, dy + vy      # defender faces left: offsets as stored (+x = away from Ken)
        if abs(cx - ex) <= arx + vrx and abs(cy - ey) <= ary + vry:
            return True
    return False

def analyze(path):
    rows = list(csv.DictReader(open(path)))
    out = []
    for n in range(1, len(rows)):
        r, p = rows[n], rows[n - 1]
        if r['p1_atkid'] == '43' and int(r['p2_hp2a']) < int(p['p2_hp2a']):
            x0 = int(p['p2_x'])                                    # defender x before hit-2 push
            c, old = int(r['p2_char']), r['p2_old'] == '1'
            # frames where Ken's box 44 is active, with Ken pos and defender boxes, as captured
            frames = [rows[k] for k in range(n, min(n + 60, len(rows)))]
            sg = 1 if int(p['p2_x']) > int(p['p1_x']) else -1     # mirror when Ken faces left
            cum2 = [0]
            for v in curve(2): cum2.append(cum2[-1] + v)
            res = {}
            for cv in range(7):
                cumx = [0]
                for v in curve(cv): cumx.append(cumx[-1] + v)
                hit = None
                for k, f in enumerate(frames):
                    d = sg * (int(f['p2_x']) - x0)                 # real displacement away from Ken (curve 2)
                    s_ = min(range(len(cum2)), key=lambda i: abs(cum2[i] - d))   # steps consumed
                    x = sg * x0 + cumx[min(s_, len(cumx) - 1)] + (d - cum2[s_])  # mirrored coords; keep residual
                    if f['p1_atkid'] == '44':
                        vb = [vul(c, old, sl, int(f['p2_' + v])) for sl, v in ((0, 'v8'), (2, 'v9'), (4, 'va'))]
                        if overlap(sg * int(f['p1_x']), int(f['p1_y']), atk(4, 44), x, int(f['p2_y']), vb):
                            hit = (k, x - sg * int(f['p1_x'])); break
                    if f['p1_atkid'] not in ('43', '44'): break
                res[cv] = hit
            out.append((n, c, old, res))
    return out

if __name__ == '__main__':
    for path in sys.argv[1:]:
        for n, c, old, res in analyze(path):
            print(path.split('/')[-1], 'frame', n, 'defender', c, 'old' if old else 'new',
                  {k: ('acerta f+%d dist %d' % v if v else 'erra') for k, v in res.items()})
