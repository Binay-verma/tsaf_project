"""Recomputation audit of journal draft v8 (a second code path by the same author, not independent review).

1. Every table copied from v7 appears verbatim in v7.
2. Table 3 (cluster tests) is recomputed from the committed cluster values with an independent sign-flip
   implementation; Tables 6 and A11 are recomputed from the raw stored forecasts.
3. Number provenance: every number in the prose (outside tables, references and links) must occur in the
   v7 manuscript or in the set of independently recomputed values. Unmatched numbers are listed.
Run from the repository root: python src/audit_journal_v8.py
"""
import csv, itertools, json, re, sys
from collections import defaultdict
from statistics import mean
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V8 = (ROOT/'manuscript/journal_v8/MANUSCRIPT.md').read_text()
V7 = (ROOT/'manuscript/integrated_review_v7/MANUSCRIPT.md').read_text()
NAMES = {'Rich Ridge': 'ridge', 'SARIMAX': 'sarimax', 'Stable LightGBM': 'lightgbm', 'Tree leaf minimum 2': 'lightgbm_capacity2',
         'Chronos-2': 'chronos', 'TimesFM-3': 'timesfm'}
problems, checked = [], 0
computed = set()


def tables(md):
    out = {}
    for m in re.finditer(r'(?m)^(Table [A-Z]?\d+)\. .*\n\n((?:\|.*\n?)+)', md):
        out[m.group(1)] = m.group(2).strip()
    return out


t8 = tables(V8)
v7_rows = set(l for l in V7.splitlines() if l.startswith('|'))
new_tables = {'Table 3', 'Table 6', 'Table A11'}
for label, body in t8.items():
    if label in new_tables:
        continue
    for line in body.splitlines():
        checked += 1
        if line not in v7_rows:
            problems.append(('row not in v7', label, line[:80]))


def rows(label):
    lines = t8[label].splitlines()
    return [[c.strip() for c in l.strip('|').split('|')] for l in lines[2:]]


# ---- Table 3: independent sign-flip on committed cluster values ----
B = list(csv.DictReader(open(ROOT/'review/journal_seven_tasks_20261031_v1/B_family_year_clusters.csv')))
groups = defaultdict(list)
for r in B:
    groups[(r['model'], r['representation'], int(r['lead']))].append(r)


def flip_p(v):
    obs = abs(sum(v)/len(v)); n = 0; hit = 0
    for s in itertools.product((1, -1), repeat=len(v)):
        n += 1
        hit += abs(sum(a*b for a, b in zip(s, v))/len(v)) >= obs-1e-12
    return hit/n


def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i]); adj = [0]*len(ps); run = 0
    for k, i in enumerate(order):
        run = max(run, min(1, (len(ps)-k)*ps[i])); adj[i] = run
    return adj


keys = sorted(groups)
p1 = {k: flip_p([float(r['typed_minus_pooled']) for r in groups[k]]) for k in keys}
h1 = dict(zip(keys, holm([p1[k] for k in keys])))
p2 = {}
for k in keys:
    by = defaultdict(dict)
    for r in groups[k]:
        by[r['family']][int(r['year'])] = float(r['typed_minus_pooled'])
    p2[k] = flip_p([by[f][2025]-by[f][2024] for f in by])
for row in rows('Table 3'):
    k = (NAMES[row[0]], row[1], 1)
    v = [float(r['typed_minus_pooled']) for r in groups[k]]
    want = [f'{mean(v):.5f}', f'{p1[k]:.4f}', f'{h1[k]:.4f}', f'{p2[k]:.4f}']
    got = [row[2], row[4], row[5], row[6]]
    checked += 4
    if got != want:
        problems.append(('Table 3', row[:2], got, want))
raw_below = sum(p < 0.05 for p in p1.values()); holm_det = sum(h < 0.05 for h in h1.values())
minp = min(p1.values()); kmin = min(p1, key=p1.get)
computed |= {str(raw_below), str(holm_det), f'{minp:.4f}', f'{h1[kmin]:.3f}'}

# ---- Tables 6 and A11 from raw stored forecasts ----


def load(path, india):
    d = list(csv.DictReader(open(ROOT/path)))
    keep = []
    for r in d:
        if india and r['version'] != 'document_aligned':
            continue
        if not india and r.get('scenario') not in ('lag7', '', None):
            continue
        if r['model'] not in NAMES.values():
            continue
        keep.append(r)
    return keep


def errors(recs):
    pred = {}
    for r in recs:
        pred[(r['model'], r['arm'], r['family'], r['state'], r['year'], r['date'][:10], r['horizon'])] = (
            float(r['prediction']), float(r['actual']), float(r['mase_scale']))
    out = []
    for rep, (t, p) in {'day': ('day5', 'pooled_day5'), 'window': ('window5', 'pooled_window5')}.items():
        for k, (pt, a, s) in pred.items():
            if k[1] != t:
                continue
            pp = pred[(k[0], p)+k[2:]][0]
            out.append(dict(model=k[0], rep=rep, family=k[2], state=k[3], year=int(k[4]), h=int(k[6]),
                            typed=abs(pt-a)/s, pooled=abs(pp-a)/s, combine=abs((pt+pp)/2-a)/s))
    return out


def bal(e, col, years=None):
    c = defaultdict(list)
    for r in e:
        if years is None or r['year'] in years:
            c[(r['model'], r['rep'], r['h'], r['family'], r['year'], r['state'])].append(r[col])
    l2 = defaultdict(list)
    for (m, rp, h, f, y, s), v in c.items():
        l2[(m, rp, h, f, y)].append(mean(v))
    l3 = defaultdict(list)
    for (m, rp, h, f, y), v in l2.items():
        l3[(m, rp, h, f)].append(mean(v))
    l4 = defaultdict(list)
    for (m, rp, h, f), v in l3.items():
        l4[(m, rp, h)].append(mean(v))
    return {k: mean(v) for k, v in l4.items()}


EI = errors(load('results/calendar_recenter_recovery_v1/analysis/breadth/event_window/predictions_compared.csv', True))
EN = errors(load('results/mta_holiday_recovery_v1/analysis/event_window/predictions_compared.csv', False))
BI = {c: bal(EI, c) for c in ['typed', 'pooled', 'combine']}
B24 = {c: bal(EI, c, {2024}) for c in ['typed', 'pooled']}
B25 = {c: bal(EI, c, {2025}) for c in ['typed', 'pooled', 'combine']}
BN = {c: bal(EN, c) for c in ['typed', 'pooled', 'combine']}
follow = {}; creg = {}
for k in B25['typed']:
    pick = 'typed' if B24['typed'][k] < B24['pooled'][k] else 'pooled'
    orc = min(B25['typed'][k], B25['pooled'][k])
    follow[k] = B25[pick][k]-orc; creg[k] = B25['combine'][k]-orc
for row in rows('Table 6'):
    k = (NAMES[row[0]], row[1], 1)
    want = [f'{BI[c][k]:.5f}' for c in ['typed', 'pooled', 'combine']] + [f'{follow[k]:.5f}', f'{creg[k]:.5f}']
    checked += 5
    if row[2:7] != want:
        problems.append(('Table 6', row[:2], row[2:7], want))
for row in rows('Table A11'):
    k = (NAMES[row[0]], row[1], 8)
    want = [f'{BN[c][k]:.5f}' for c in ['typed', 'pooled', 'combine']]
    checked += 3
    if row[2:5] != want:
        problems.append(('Table A11', row[:2], row[2:5], want))
worse = sum(v > 0 for v in follow.values()); beats = sum(B25['combine'][k] < B25['pooled' if B24['typed'][k] >= B24['pooled'][k] else 'typed'][k] for k in follow)
computed |= {str(worse), str(beats), f'{mean(follow.values()):.4f}', f'{mean(creg.values()):.4f}'}
for B, tag in [(BI, 'i'), (BN, 'n')]:
    reg = [B['combine'][k]-min(B['typed'][k], B['pooled'][k]) for k in B['typed']]
    bound = [abs(B['typed'][k]-B['pooled'][k])/2 for k in B['typed']]
    below = sum(B['combine'][k] < min(B['typed'][k], B['pooled'][k]) for k in B['typed'])
    computed |= {f'{mean(reg):.4f}', f'{mean(bound):.4f}', str(below)}
    assert all(B['combine'][k] <= max(B['typed'][k], B['pooled'][k])+1e-12 for k in B['typed'])

# ---- number provenance in prose ----
prose = []
for line in V8.split('## References')[0].splitlines():
    if line.startswith('|') or line.startswith('!['):
        continue
    line = re.sub(r'https?://\S+', '', line)
    line = re.sub(r'\b(Table|Figure|Section|Sections|Tables|Figures)\s+[A-Z]?\d+(\s*(and|to|–)\s*[A-Z]?\d+)*', '', line)
    line = re.sub(r'\[\d+(,\s*\d+)*\]', '', line)
    prose.append(line)
text = '\n'.join(prose)
text = re.sub(r'(?m)^#+ [\d.]+ ', '# ', text)          # section numbers in headings
text = text.replace('follow-2024', 'follow-rule')     # rule label, not a number
# values traced to other committed sources, each checked against that source
proto = json.loads((ROOT/'results/cluster_inference_v1/protocol.json').read_text())
assert '2/1024' in proto['interpretation'] and '2/32' in proto['interpretation'] and '2/16' in proto['interpretation'] and 'alpha 0.05' in proto['multiplicity']
computed |= {'0.05', f'{2/32:.4f}', f'{2/16:.3f}', '1,024'}
eng = (ROOT/'src/breadth_model_engine_v1.py').read_text()
assert re.search(r'order=\(1, 0, 0\),\s*seasonal_order=\(1, 0, 0, 7\)', eng)
computed |= {'1,0,0', '1,0,0,7'}
assert '31 Oct–11 Nov 2026' in (ROOT/'README.md').read_text()
computed |= {'31'}
assert 'all-58' in V7
computed |= {'58'}
tok = lambda s: set(m.strip(',').rstrip('.') for m in re.findall(r'-?\d[\d,]*(?:\.\d+)?', s))
v7_tokens = tok(V7)
STRUCTURAL = {str(i) for i in range(1, 10)} | {'8'}
unmatched = sorted(t for t in tok(text) if t not in v7_tokens and t not in computed and t not in STRUCTURAL)
checked += len(tok(text))
if unmatched:
    problems.append(('numbers in prose not traced to v7 or recomputation', unmatched))

res = dict(checked_items=checked, problems=problems, passed=not problems)
json.dump(res, open(ROOT/'manuscript/journal_v8/recomputation_v8_audit.json', 'w'), indent=1, default=str)
print(json.dumps(res, indent=1, default=str)[:4000])
sys.exit(0 if not problems else 1)
