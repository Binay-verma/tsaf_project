"""Build journal-format draft v9 from audited sources (v8 content plus the longer panel: Stage A, Stage B).

- Tables from v7 are copied verbatim (rows untouched); only captions and numbering change.
- New tables and every new number are computed here from committed analysis files.
- Every new number is computed here from committed Stage A/B analysis files and asserted where it is restated.
Run from the repository root: python src/build_journal_v9.py
"""
import csv, datetime, hashlib, json, re, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V7 = ROOT/'manuscript/integrated_review_v7'
OUT = ROOT/'manuscript/journal_v9'
V8 = ROOT/'manuscript/journal_v8'
CI = ROOT/'results/cluster_inference_v1/analysis'
RC = ROOT/'results/representation_combination_v2/analysis'
NAMES = {'ridge': 'Rich Ridge', 'sarimax': 'SARIMAX', 'lightgbm': 'Stable LightGBM', 'lightgbm_capacity2': 'Tree leaf minimum 2',
         'chronos': 'Chronos-2', 'timesfm': 'TimesFM-3'}
ORDER = ['ridge', 'sarimax', 'lightgbm', 'lightgbm_capacity2', 'chronos', 'timesfm']


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def read(p):
    return list(csv.DictReader(open(p)))


def f5(x):
    return f'{float(x):.5f}'


v7 = (V7/'MANUSCRIPT.md').read_text()


def table(label):
    """Header, separator and rows of a v7 table, verbatim."""
    block = v7.split(f'\n{label}. ', 1)[1].split('\n\n', 2)[1]
    rows = [l for l in block.splitlines() if l.startswith('|')]
    assert len(rows) >= 3, label
    return '\n'.join(rows)


# ---------------- new numbers ----------------
ci = json.load(open(CI/'summary.json'))
rc = json.load(open(RC/'summary.json'))
ind = read(CI/'india_cluster_tests.csv')
tf = next(r for r in ind if r['model'] == 'timesfm' and r['representation'] == 'day' and r['lead'] == '1')
assert float(tf['p_T1']) == ci['T1']['min_raw_p']
comb_i = read(RC/'india_combination.csv'); comb_n = read(RC/'nyc_combination.csv')
dec = read(RC/'india_2025_decision_rules.csv')
half_gap_i = sum(abs(float(r['typed'])-float(r['pooled']))/2 for r in comb_i)/len(comb_i)
half_gap_n = sum(abs(float(r['typed'])-float(r['pooled']))/2 for r in comb_n)/len(comb_n)
ties_n = sum(float(r['typed']) == float(r['pooled']) for r in comb_n)
assert rc['India']['combine_below_worse'] == 36 and rc['NYC']['combine_below_worse'] + ties_n == 36
nyc_ci_excl = ci['t_interval_excludes_zero']['NYC']
N = dict(T1_raw=ci['T1']['raw_below_005'], T1_holm=ci['T1']['holm_detected'], T1_min=f"{ci['T1']['min_raw_p']:.4f}",
         tf_holm=f"{float(tf['holm_T1']):.3f}", T2_raw=ci['T2']['raw_below_005'], T3_raw=ci['T3']['raw_below_005'],
         ci_i=ci['t_interval_excludes_zero']['India'], ci_n=nyc_ci_excl,
         below_both_i=rc['India']['combine_below_both'], below_both_n=rc['NYC']['combine_below_both'],
         regret_i=f"{rc['India']['mean_combine_regret']:.4f}", bound_i=f'{half_gap_i:.4f}',
         regret_n=f"{rc['NYC']['mean_combine_regret']:.4f}", bound_n=f'{half_gap_n:.4f}', ties_n=ties_n,
         worse=rc['India']['india_2025']['follow_picked_worse'], follow_r=f"{rc['India']['india_2025']['mean_follow_regret']:.4f}",
         comb_r=f"{rc['India']['india_2025']['mean_combine_regret']:.4f}", beats=rc['India']['india_2025']['combine_beats_follow'],
         holm_c=rc['India']['holm_detected_vs_typed']+rc['India']['holm_detected_vs_pooled']+rc['NYC']['holm_detected_vs_typed']+rc['NYC']['holm_detected_vs_pooled'])
assert N['holm_c'] == 0 and N['T1_holm'] == 0

# post-hoc descriptive numbers requested by the internal referee check (not part of any registered protocol)
from statistics import mean, median
from math import comb
N['holm_floor36'] = f'{36*2/1024:.3f}'; N['holm_floor12'] = f'{12*min(float(r["p_T1"]) for r in ind if r["lead"] == "1"):.3f}'
N['expected_raw'] = f'{36*0.05:.1f}'
fr = [float(r['follow_regret']) for r in dec]; cr = [float(r['combine_regret']) for r in dec]
N['random_r'] = f"{mean(abs(float(r['typed'])-float(r['pooled']))/2 for r in dec):.4f}"
N['med_follow'] = f'{median(fr):.4f}'; N['med_comb'] = f'{median(cr):.4f}'; N['max_follow'] = f'{max(fr):.3f}'; N['max_comb'] = f'{max(cr):.3f}'
w = sum(float(r['combine']) < float(r['follow_2024']) for r in dec); assert w == N['beats']
N['sign_p'] = f'{min(1, 2*sum(comb(36, k) for k in range(max(w, 36-w), 37))/2**36):.2f}'
def fixed(rows, col):
    return [float(r[col])-float(r['oracle']) for r in rows]
for tag, rows in [('i', comb_i), ('n', comb_n)]:
    t, p, c = fixed(rows, 'typed'), fixed(rows, 'pooled'), [float(r['combine_regret']) for r in rows]
    N[f'mt_{tag}'], N[f'mp_{tag}'], N[f'mc_{tag}'] = f'{mean(t):.4f}', f'{mean(p):.4f}', f'{mean(c):.4f}'
    N[f'xt_{tag}'], N[f'xp_{tag}'], N[f'xc_{tag}'] = f'{max(t):.4f}', f'{max(p):.4f}', f'{max(c):.4f}'
    assert max(c) < min(max(t), max(p))
# controls table (stored registered metrics)
MI = [r for r in read(ROOT/'results/calendar_recenter_recovery_v1/analysis/breadth/event_window/metrics_balanced.csv') if r['version'] == 'document_aligned' and r['horizon'] == '1']
MN = [r for r in read(ROOT/'results/mta_holiday_recovery_v1/analysis/event_window/metrics_balanced.csv') if r['horizon'] == '8']
def mv(rows, m, a):
    x = [r for r in rows if r['model'] == m and r['arm'] == a]
    return f5(x[0]['MASE']) if x else '–'
t_ctl = ['| Source | Model | History | Cal. | + zeros | Placebo | Typed | Pooled |', '| ------- | --------------- | -------- | -------- | -------- | -------- | -------- | -------- |']
for src, rows in [('India', MI), ('NYC', MN)]:
    for m in ORDER:
        t_ctl.append(f"| {src} | {NAMES[m]} | {mv(rows, m, 'history')} | {mv(rows, m, 'calendar')} | {mv(rows, m, 'zero5')} | {mv(rows, m, 'placebo_day5')} | {mv(rows, m, 'day5')} | {mv(rows, m, 'pooled_day5')} |")
t_ctl.append(f"| NYC | Last value | {mv(MN, 'last', 'history')} | – | – | – | – | – |")
t_ctl.append(f"| NYC | Seasonal naive | {mv(MN, 'seasonal', 'history')} | – | – | – | – | – |")

# ---------------- new tables ----------------
t_ci = ['| Model | Rep. | Mean (10 clusters) | 95% t interval | Sign-flip p | Holm p | Year-change p |', '| --- | --- | --- | --- | --- | --- | --- |']
for m in ORDER:
    for rep in ['day', 'window']:
        r = next(x for x in ind if x['model'] == m and x['representation'] == rep and x['lead'] == '1')
        t_ci.append(f"| {NAMES[m]} | {rep} | {f5(r['mean'])} | {f5(r['t_low'])} to {f5(r['t_high'])} | {float(r['p_T1']):.4f} | {float(r['holm_T1']):.4f} | {float(r['p_T2']):.4f} |")
t_comb = ['| Model | Rep. | Typed | Pooled | Average | 2025: follow-2024 regret | 2025: average regret |', '| --- | --- | --- | --- | --- | --- | --- |']
for m in ORDER:
    for rep in ['day', 'window']:
        r = next(x for x in comb_i if x['model'] == m and x['representation'] == rep and x['horizon'] == '1')
        y = next(x for x in dec if x['model'] == m and x['representation'] == rep and x['horizon'] == '1')
        t_comb.append(f"| {NAMES[m]} | {rep} | {f5(r['typed'])} | {f5(r['pooled'])} | {f5(r['combine'])} | {f5(y['follow_regret'])} | {f5(y['combine_regret'])} |")
t_comb_n = ['| Model | Rep. | Typed | Pooled | Average |', '| --- | --- | --- | --- | --- |']
for m in ORDER:
    for rep in ['day', 'window']:
        r = next(x for x in comb_n if x['model'] == m and x['representation'] == rep and x['horizon'] == '8')
        t_comb_n.append(f"| {NAMES[m]} | {rep} | {f5(r['typed'])} | {f5(r['pooled'])} | {f5(r['combine'])} |")

# ---------------- longer panel: Stage A and Stage B (new in v9) ----------------
SA = ROOT/'results/longer_panel_stage_a_v1'
SB = ROOT/'results/longer_panel_stage_b_v1'
HYP = ROOT/'results/model_class_hypothesis_v1/registration.json'
sa = json.load(open(SA/'analysis/summary.json'))
sad = json.load(open(SA/'design_summary.json'))
sbd = json.load(open(SB/'design_summary.json'))
sb = json.load(open(SB/'analysis/summary.json'))
tvp = read(SA/'analysis/typed_vs_pooled.csv')
ctl = read(SA/'analysis/controls.csv')
hyp_t = read(SB/'analysis/hypothesis_tests.csv')
hyp_s = read(SB/'analysis/sensitivity_without_2020.csv')
sbb = read(SB/'analysis/balanced.csv')
assert sad['event_cases'] == 1056 and sad['ordinary_cases'] == 432 and sad['family_year_clusters'] == 20
assert sbd['event_cases'] == 327 and sbd['dropped'] == 0 and sbd['clusters'] == 15
assert sb['decisions'] == {'H1': 'NOT CONFIRMED', 'H2': 'CONFIRMED', 'H1b (secondary)': 'CONFIRMED'}
assert sb['sensitivity_without_2020'] == {'H1': 'NOT CONFIRMED', 'H2': 'CONFIRMED', 'H1b (secondary)': 'NOT CONFIRMED'}
for f, h in sa['outputs'].items():
    assert sha(SA/'analysis'/f) == h, f
for f, h in sb['outputs'].items():
    assert sha(SB/'analysis'/f) == h, f
LOCAL = ['ridge', 'sarimax', 'lightgbm', 'lightgbm_capacity2']
YA = [2022, 2023, 2024, 2025]


def g(rows, **k):
    x = [r for r in rows if all(str(r[a]) == str(b) for a, b in k.items())]
    assert len(x) == 1, (k, len(x))
    return x[0]


def s4(x):
    if float(x) == 0.0:
        return '0.0000'
    return f'{float(x):+.4f}'.replace('+-', '-').replace('-', '−')


SHORT = {'ridge': 'Ridge', 'sarimax': 'SARIMAX', 'lightgbm': 'LGBM', 'lightgbm_capacity2': 'LGBM-2', 'chronos': 'Chronos-2', 'timesfm': 'TimesFM-3'}
t_sa = ['| Model | Rep. | All years | 2022 | 2023 | 2024 | 2025 | Same sign | p | Holm p |',
        '| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |']
for m in LOCAL:
    for rep in ['day', 'window']:
        r = g(tvp, model=m, representation=rep, lead=1)
        t_sa.append(f"| {SHORT[m]} | {rep} | {s4(r['typed_minus_pooled'])} | "
                    + ' | '.join(s4(r[f'year_{y}']) for y in YA)
                    + f" | {r['years_same_sign']}/4 | {float(r['p_signflip']):.4f} | {float(r['holm_primary']):.3f} |")
ARMS_C = ['calendar', 'zero5', 'placebo_day5', 'day5', 'pooled_day5', 'window5', 'pooled_window5']
t_sactl = ['| Model | Calendar | + zeros | Placebo | Typed day | Pooled day | Typed window | Pooled window |', '| --- | --- | --- | --- | --- | --- | --- | --- |']
for m in LOCAL:
    r = g(ctl, model=m, lead=1)
    t_sactl.append(f"| {NAMES[m]} | " + ' | '.join(f5(r[a]) for a in ARMS_C) + ' |')
ctl_gap = max(abs(float(g(ctl, model=m, lead=1)[a])-float(g(ctl, model=m, lead=1)['calendar'])) for m in LOCAL for a in ['zero5', 'placebo_day5'])
ctl_gap_w = max(abs(float(g(ctl, model=m, lead=1)[a])-float(g(ctl, model=m, lead=1)['calendar'])) for m in LOCAL for a in ['zero5', 'placebo_day5', 'placebo_window5'])
sup = [r for r in tvp if r['supported'] == 'True']
assert len(sup) == 1 and sup[0]['model'] == 'lightgbm' and sup[0]['representation'] == 'day' and sup[0]['lead'] == '1'
SAN = dict(lgb=g(tvp, model='lightgbm', representation='day', lead=1), lgb2=g(tvp, model='lightgbm_capacity2', representation='day', lead=1),
           sar=g(tvp, model='sarimax', representation='day', lead=1), rid=g(tvp, model='ridge', representation='day', lead=1))
raw24 = sum(float(r['p_signflip']) < 0.05 for r in tvp)
assert raw24 == sa['all24_raw_below_005'] == 6 and sa['all24_holm_below_005'] == 0
mr, xr = sa['mean_regret'], sa['max_regret']

# Stage B, per-year contrasts for every local model (reported, H3 included)
sys.path.insert(0, str(ROOT/'src'))
from longer_panel_analysis_stage_b_v1 import load as load_b, clusters as clusters_b
cb = clusters_b(load_b(), [2019, 2020, 2021])
SBY = {}
for m in LOCAL:
    diff = cb[(m, 'day5', 1)]-cb[(m, 'pooled_day5', 1)]
    SBY[m] = {'mean': float(diff.mean()), **{y: float(diff.xs(y, level='year').mean()) for y in [2019, 2020, 2021]}}
h2 = g(hyp_t, hypothesis='H2'); h1 = g(hyp_t, hypothesis='H1'); h1b = g(hyp_t, hypothesis='H1b (secondary)')
h2s = g(hyp_s, hypothesis='H2'); h1bs = g(hyp_s, hypothesis='H1b (secondary)')
assert abs(SBY['sarimax']['mean']-float(h2['typed_minus_pooled'])) < 1e-12 and SBY['lightgbm']['mean'] == 0.0
t_sb = ['| Hyp. | Model | All years | 2019 | 2020 | 2021 | One-sided p | Holm p | Decision | Without 2020 |',
        '| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |']
for r, s in [(h1, g(hyp_s, hypothesis='H1')), (h2, h2s), (h1b, h1bs)]:
    dec = r['decision'].lower() if r['hypothesis'] != 'H1b (secondary)' else ('meets rule, unadjusted' if r['decision'] == 'CONFIRMED' else 'does not meet rule')
    dec_s = s['decision'].lower() if r['hypothesis'] != 'H1b (secondary)' else ('meets rule, unadjusted' if s['decision'] == 'CONFIRMED' else 'does not meet rule')
    t_sb.append(f"| {r['hypothesis'].replace(' (secondary)', '')} | {SHORT[r['model']]} | {s4(r['typed_minus_pooled'])} | "
                + ' | '.join(s4(r[f'year_{y}']) for y in [2019, 2020, 2021])
                + f" | {float(r['p_one_sided']):.4f} | {(f'{float(r['holm']):.4f}' if r['holm'] else '–')} | {dec} | {dec_s} |")
t_sbctl = ['| Model | Calendar | + zeros | Placebo | Typed day | Pooled day |', '| --- | --- | --- | --- | --- | --- |']
for m in LOCAL:
    t_sbctl.append(f"| {NAMES[m]} | " + ' | '.join(f5(g(sbb, model=m, arm=a, horizon=1)['MASE']) for a in ['calendar', 'zero5', 'placebo_day5', 'day5', 'pooled_day5']) + ' |')
lgb_arms = {a: float(g(sbb, model='lightgbm', arm=a, horizon=1)['MASE']) for a in ['calendar', 'zero5', 'placebo_day5', 'day5', 'pooled_day5']}
assert len(set(lgb_arms.values())) == 1
SB_N = dict(h2=s4(h2['typed_minus_pooled']), h2p=f"{float(h2['p_one_sided']):.4f}", h2h=f"{float(h2['holm']):.4f}",
            h2s=s4(h2s['typed_minus_pooled']), h2sh=f"{float(h2s['holm']):.4f}",
            h1b=s4(h1b['typed_minus_pooled']), h1bp=f"{float(h1b['p_one_sided']):.4f}", h1bs=s4(h1bs['typed_minus_pooled']), h1bsp=f"{float(h1bs['p_one_sided']):.4f}",
            ridge=s4(SBY['ridge']['mean']), lgb=f5(lgb_arms['calendar']))
# foundation models over Stage A (Kaggle run, exploratory)
FD = ROOT/'results/longer_panel_foundation_v1/analysis'
fs = json.load(open(FD/'summary.json'))
for f, h in fs['outputs'].items():
    assert sha(FD/f) == h, f
assert fs['reproduction']['passed'] and fs['reproduction']['within_tolerance'] == fs['reproduction']['rows'] == 1584
ftv = read(FD/'typed_vs_pooled.csv'); fct = read(FD/'controls.csv')
t_fd = ['| Model | Rep. | Typed | Pooled | All years | 2022 | 2023 | 2024 | 2025 | Same sign | p | Holm p |', '| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |']
for m in ['chronos', 'timesfm']:
    for rep in ['day', 'window']:
        r = g(ftv, model=m, representation=rep, lead=1)
        t_fd.append(f"| {SHORT[m]} | {rep} | {f5(r['typed'])} | {f5(r['pooled'])} | {s4(r['typed_minus_pooled'])} | " + ' | '.join(s4(r[f'year_{y}']) for y in YA)
                    + f" | {r['years_same_sign']}/4 | {float(r['p_signflip']):.4f} | {float(r['holm_primary']):.3f} |")
fsup = [r for r in ftv if r['supported'] == 'True']
assert len(fsup) == 1 and fsup[0]['model'] == 'timesfm' and fsup[0]['representation'] == 'day' and fsup[0]['lead'] == '1'
FN = dict(tf=g(ftv, model='timesfm', representation='day', lead=1), ch=g(ftv, model='chronos', representation='day', lead=1),
          tfc=g(fct, model='timesfm', lead=1), chc=g(fct, model='chronos', lead=1))
f_gap = max(abs(float(FN[k][a])-float(FN[k]['calendar'])) for k in ['tfc', 'chc'] for a in ['zero5', 'placebo_day5', 'placebo_window5'])
f_raw = sum(float(r['p_signflip']) < 0.05 for r in ftv)
# frozen prospective episodes (scored 13 Nov 2026 with the first complete actual vintage)
P1 = ROOT/'results/prospective_20261030_scoring_v1'; P2 = ROOT/'results/prospective_chronos_20261031_scoring_v1'; PI = ROOT/'results/prospective_interval_20261030_scoring_v1'
fz1 = json.load(open(ROOT/'results/prospective_20261030_v1/freeze.json')); fz2 = json.load(open(ROOT/'results/prospective_chronos_20261031_v1/freeze.json'))
rc2 = json.load(open(ROOT/'results/prospective_chronos_20261031_v1/public_receipt.json'))
col1 = json.load(open(P1/'collection.json'))
assert col1['scored_predictions_sha256'] == sha(P1/'scored_predictions.csv') and fz1['predictions_sha256'] == json.load(open(P1/'audit.json'))['frozen_predictions_sha256']
m1 = {r['model']: float(r['MASE']) for r in read(P1/'macro_metrics.csv')}
m2 = {r['model']: float(r['MASE']) for r in read(P2/'metrics_macro.csv')}
iv = read(PI/'metrics_macro.csv')
assert fz1['eligible_rows'] == 216 and fz2['eligible_rows'] == 66
PN = {'timesfm3_calendar': 'TimesFM-3, calendar', 'timesfm3_history': 'TimesFM-3, history only', 'chronos2_calendar': 'Chronos-2, calendar', 'chronos2_history': 'Chronos-2, history only',
      'ridge_rich_calendar_monthly': 'Rich Ridge, calendar', 'lightgbm_rich_calendar_monthly': 'Stable LightGBM, calendar', 'last_value': 'Last value', 'weekly_repeat': 'Weekly repeat'}
t_pro = ['| Model | Episode 1: 31 Oct–11 Nov (36 cases) | Episode 2: 1–11 Nov (33 cases) |', '| --- | --- | --- |']
for k in ['chronos2_calendar', 'chronos2_history', 'timesfm3_calendar', 'timesfm3_history', 'ridge_rich_calendar_monthly', 'lightgbm_rich_calendar_monthly', 'last_value', 'weekly_repeat']:
    t_pro.append(f"| {PN[k]} | {(f'{m1[k]:.3f}' if k in m1 else '–')} | {m2[k]:.3f} |")
cov = {(r['model'], r['arm']): float(r['coverage80']) for r in iv}
PRO = dict(best2=min(m2, key=m2.get), lo1=min(m1.values()), hi1=max(m1.values()), cov_lo=min(cov.values()), cov_hi=max(cov.values()),
           cov_native=cov[('timesfm3_calendar', 'native')])
assert PRO['best2'] == 'chronos2_calendar' and min(m1, key=m1.get) == 'ridge_rich_calendar_monthly'
COMMITS = {'Stage A protocol': 'd60df30', 'Stage A results': 'b2bebc3', 'hypothesis': 'dec1274', 'Stage B protocol': '65d1880', 'Stage B results': '395c378', 'foundation protocol': '5f71883', 'foundation results': '9064eea', 'prospective scores': 'f4a3f74'}
for k, c in COMMITS.items():
    assert subprocess.run(['git', 'cat-file', '-e', c], cwd=ROOT).returncode == 0, k
CT = {k: subprocess.run(['git', 'show', '-s', '--format=%cI', c], cwd=ROOT, capture_output=True, text=True).stdout.strip() for k, c in COMMITS.items()}


def per_year_figure(path):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    years = [2019, 2020, 2021, 2022, 2023, 2024, 2025]
    fig, ax = plt.subplots(figsize=(6.4, 3.2))
    w = 0.2; hatch = ['', '//', '..', 'xx']; col = ['0.85', '0.55', '0.3', '0.05']
    for i, m in enumerate(LOCAL):
        a = g(tvp, model=m, representation='day', lead=1)
        v = [SBY[m][y] for y in years[:3]] + [float(a[f'year_{y}']) for y in YA]
        ax.bar(np.arange(7)+(i-1.5)*w, v, w, color=col[i], edgecolor='black', linewidth=0.4, hatch=hatch[i], label=NAMES[m])
    ax.axhline(0, color='black', lw=0.6); ax.axvline(2.5, color='0.4', ls='--', lw=0.7)
    ax.set_xticks(range(7)); ax.set_xticklabels(years); ax.set_ylabel('Typed − pooled MASE (lead 1, day)')
    ax.text(1, -0.108, 'Stage B: Maharashtra (confirmatory)', ha='center', fontsize=7); ax.text(4.5, -0.108, 'Stage A: three states (exploratory)', ha='center', fontsize=7)
    ax.set_ylim(-0.118, 0.14); ax.legend(fontsize=7, ncol=4, loc='lower center', bbox_to_anchor=(0.5, 1.0), frameon=False)
    fig.tight_layout(); fig.savefig(path.with_suffix('.png'), dpi=200); fig.savefig(path.with_suffix('.pdf'))

# ---------------- manuscript ----------------
TITLE = 'Typed or pooled festival indicators? The answer depends on the model class: Indian electricity evidence with a registered follow-up test'


md = f"""# {TITLE}

Binay Verma

Affiliation: __________ . Corresponding author email: __________ .

**Draft for supervisor review (journal format, version 9). Not submitted.**

## Abstract

Forecasters who add festival indicators to a model must choose between one indicator per festival (typed) and one shared indicator (pooled). We compare the two for daily electricity in three Indian states, with matched zero-channel and placebo controls, for two foundation models and four local models. Over four event years (1,056 festival-window cases, 20 family-year clusters), the better representation depends on the model: LightGBM (Holm p {float(SAN['lgb']['holm_primary']):.3f}) and TimesFM-3 (Holm p {float(FN['tf']['holm_primary']):.3f}) are better with a pooled flag, SARIMAX leans towards typed flags, and Ridge and Chronos-2 show no ordering. Stated as a hypothesis and committed to the repository before further data were evaluated, the SARIMAX preference held on Maharashtra event years 2019–2021 (Holm p {SB_N['h2h']}, all three years). The LightGBM test was uninformative, because the selected trees never split on the rare flags; the LightGBM advantage for pooling may reflect that only the pooled flag has enough flagged days to be used. Choosing the representation from last year's winner picked the worse one in {sa['follow_picked_worse']} of {sa['decision_cells']} cases, while averaging the two forecasts gave the smallest worst-case regret.

**Keywords:** holiday effects; event covariates; load forecasting; time-series foundation models; forecast combination; pre-registration.

## Highlights

- Typed and pooled festival flags compared with matched zero and placebo controls
- SARIMAX prefers typed flags; LightGBM and TimesFM-3 do better with a pooled flag
- The SARIMAX preference held in a registered test on three further years
- Trees ignore flags with fewer flagged days than their minimum leaf size
- Averaging typed and pooled forecasts limits the worst-case loss

## 1. Introduction

Holidays and festivals are rare, recurring and heterogeneous. A forecaster who adds them to a model faces a choice that predates modern machine learning: give each named event its own indicator, so that each can have its own response, or pool them into one indicator, so that sparse events borrow strength from one another. In load forecasting the trade-off is familiar [9, 10]. Covariate-informed time-series foundation models (TSFMs) such as Chronos-2 [6] and TimesFM-3 [7] reopen it in a new form, because the model is not re-estimated: the forecaster controls only which channels are passed and how they are encoded [1, 2].

An earlier version of this study, with two event years and 10 family-year clusters, found that the ordering changed between years, models and data sources and that no ordering could be confirmed. This version doubles the evaluation period and adds a confirmatory step. Our contributions are:

1. **A matched comparison.** Typed and pooled festival indicators are compared for two pinned TSFMs and four local models on identical cases, with a calendar baseline, an equal-dimension zero-channel control and weekday-shifted placebos, so that gains from adding channels and gains from festival information can be separated (Sections 3 and 4).
2. **A model-class pattern over four years.** With 1,056 festival-window cases in 2022–2025 and hand-checked state calendars, the preferred representation depends on the model: SARIMAX leans towards typed flags, while LightGBM and TimesFM-3 do better with one pooled flag (Sections 5.2 and 5.3).
3. **A registered follow-up test.** The pattern was written down as a hypothesis and committed before three further event years were evaluated; the SARIMAX part held, and the LightGBM part could not be tested because the selected trees did not use any festival flag (Section 5.4).
4. **Decision rules for uncertain orderings.** Following last year's winner often picks the worse representation, and an equal-weight average of the two representations limits the worst case (Section 6).

We do not propose a new architecture, claim causal holiday effects or claim contamination-free testing of pretrained models. Section 2 reviews related work, Section 3 the data and calendars, Section 4 the models and evaluation, Sections 5 and 6 the results, and Sections 7 to 9 reproducibility, limitations and conclusions.

## 2. Related work

**Holidays in load forecasting.** Ziel [9] compared one shared holiday dummy, grouped dummies and a separate dummy for each holiday for German load. He reported that many additional per-holiday dummies did not seem to improve on one additional dummy, with univariate results mixed by holiday type; in his multivariate comparison three models were not significantly worse than the best model forecast, M-RpH (a replacing design with one dummy per holiday), and the holiday-as-Saturday and holiday-as-Sunday designs were in most cases significantly worse than the best approach. Arora and Taylor [10] treat special days with rule-based seasonal ARMA models. Moving Indian holidays have been modelled in official manufacturing statistics [3].

**Covariates in foundation models.** Kreusel et al. [1] examine calendar encodings in Chronos-2 and TimesFM-3. Alipour et al. [2] learn impact-driven event representations from residual responses. Kaljevic et al. [4] benchmark TSFMs for load forecasting under covariate uncertainty.

**Forecast combination and evaluation.** Averaging forecasts goes back to Bates and Granger [11]; simple equal weights often perform as well as estimated weights [12]. We use equal weights only as a hedge between two representations. Meyer et al. [5] show that information leakage can affect TSFM evaluation. Pre-registration [15] separates hypotheses formed from data from those tested on new data.

Our study does not introduce typed or pooled indicators, which are established. It examines how that choice behaves under a fixed channel budget with zero and placebo controls, across model classes, and what a forecaster should do when the ordering is uncertain.

## 3. Data and calendars

### 3.1 Electricity data

The target is daily energy met/supplied in GWh for Delhi, Karnataka and Maharashtra, from a GRID-INDIA/POSOCO compilation. It is not latent unconstrained demand, household consumption or hourly peak load. Days with a missing or non-positive value are never scored. All outcomes used here were public and many had been inspected before the analyses were designed, so every result is retrospective; the registrations described in Section 4.4 fix the analysis before it is run, not before the data exist.

### 3.2 Festival calendars

Five festival families are used: Holi, Dussehra, Ganesh Chaturthi, Ugadi/Gudi Padwa and Diwali, each in the states where it is a listed holiday; Diwali has a main anchor and a state-listed second day. Each calendar row records its source document and was checked by hand before use, and the code refuses unchecked rows. For 2022–2025, twelve retained annual state documents support an internal review of all 58 named dates: 54 match the declared family, two are explicit shared-national-main exceptions, one Karnataka 2025 date did not match, and one Maharashtra 2022 Gudi Padwa date could not be corroborated from the retained one-page schedule. The Karnataka notification labels Vijayadasami on 1 October 2025 while the original ledger used 2 October (Gandhi Jayanthi); a separately registered flag-only correction and recentering are reported in the supplement. Rows for 2017–2021 were added for the longer panel from state notifications or third-party reproductions of them (for Maharashtra, only 2019 is from the official document) and checked by the author before the corresponding stage was registered; the Maharashtra 2017–2019 rows were checked after the hypothesis of Section 5.4 had been formed. A check found, for example, that a reposted 2019 Maharashtra list gave 26 October for Laxmi Pujan, while the official date was 27 October. Visible notification dates are not certified first-publication histories, so it is not established that every flag was publicly known at each forecast origin.

### 3.3 Evaluation cohorts

For each festival anchor a ±3-day window is formed, overlapping windows are merged, and every target date in the window is forecast at leads 1, 7 and 14. Family-year combinations (clusters), not rows, are the effective event units. A seasonal ordinary sample takes the first eligible rotating weekday per month, state and year, outside festival windows. Table 1 lists the cohorts.

Table 1. Evaluation cohorts.

| Cohort | Role | States | Event years | Event cases | Ordinary cases | Clusters | Models |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Two-year (Section 5.1) | exploratory | 3 | 2024–2025 | 528 | 216 | 10 | 6 |
| Stage A (Sections 5.2–5.3) | exploratory | 3 | 2022–2025 | {sad['event_cases']:,} | {sad['ordinary_cases']} | {sad['family_year_clusters']} | 6 |
| Stage B (Section 5.4) | confirmatory | Maharashtra | 2019–2021 | {sbd['event_cases']} | – | {sbd['clusters']} | 4 local |

### 3.4 NYC transit replication

The MTA daily ridership dataset (identifier sayj-mze2) provides Subway and Bus estimated counts. The protocol was committed before the evaluation records were acquired. The 84 event cases cover complete ±3-day windows around Yom Kippur and Columbus Day 2026, two modes and three decision leads; a fixed seven-day observation buffer maps decision leads 1/7/14 to model steps 8/14/21. Two observances in one city support a bounded robustness check only. A further check on England/Wales transmission demand (NESO) concerns observation delay, not holidays (Appendix Table A15).

## 4. Models, representations and evaluation

### 4.1 Models

Chronos-2 and TimesFM-3 use pinned code and weights, 730 prior target days, fixed seeds, two CPU threads and no task fine-tuning. The four local specifications are a rich Ridge regression, a float32 LightGBM [14], a minimum-leaf-2 LightGBM sensitivity ("tree leaf minimum 2"), and SARIMAX(1,0,0)(1,0,0,7). Ridge and LightGBM use 27 past-only history features; their parameters are selected for each year, state and lead on the 180 days before the event year, with the ordinary calendar only and purged future labels, and are then shared by all arms, so arms differ only in their festival channels. Local models are refitted monthly while foundation models are frozen, so model rankings do not isolate architecture.

### 4.2 Representations and controls

Every arm keeps 13 ordinary calendar channels (seven weekday indicators and three annual harmonic pairs). Apart from the calendar arm, each main arm adds five channels:

- **calendar** (no festival information) and **calendar + five zeros** (equal dimension, no information);
- **typed day / typed window**: one indicator per family, on the festival day or on its ±3-day window;
- **pooled day / pooled window**: one shared indicator plus four zero channels;
- **typed day / window placebos**: the same indicators shifted by fixed seeded weekday-preserving offsets of four to six weeks that avoid true windows.

Three further local-model arms adapt Ziel's designs [9] (Section 5.5): **hSun** treats each anchor day as a Sunday; **Rph** adds the pooled day flag and sets all seven weekday dummies to zero on flagged days; **RpH** does the same with the five typed flags.

### 4.3 Error measure and tests

The error measure is MASE [13] with a fixed pre-year scale (the mean absolute weekly difference over the previous 730 days); imputed labels are never scored. Event summaries average errors within state/year/family, then states within year, years within family, and families equally. The main contrast is typed minus pooled MASE, so positive values favour pooling.

Because rows within a festival window are correlated, contrasts are tested with exact sign-flip permutation tests on family-year cluster means, enumerating all 2^n sign assignments, and Holm-adjusted [16]; tests are two-sided except the registered Stage B tests, which are one-sided in the hypothesised direction. With 10 clusters (Section 5.1) the smallest attainable two-sided p is 2/1,024, so Holm over 36 cells cannot go below {N['holm_floor36']}; with 20 clusters (Stage A) it is 2/2^20 (about 1.9 × 10^-6), and Holm is applied over the eight lead-1 cells. A sign-flip test assumes cluster differences are symmetric about zero under the null; clusters in the same year share weather and source vintage, so the tests are approximate.

### 4.4 Registration sequence

Each stage's protocol was committed to the repository before that stage's selection and forecasts were run, and every worker checks the hashes of its inputs against the registered protocol before running; the 2024–2025 forecasts already existed when Stage A was registered. The order matters for interpreting Section 5: the Stage A protocol was committed at {CT['Stage A protocol'][11:16]} UTC on 11 November 2026 and its results at {CT['Stage A results'][11:16]}; the model-class hypothesis (results/model_class_hypothesis_v1) was formed from those results and committed at {CT['hypothesis'][11:16]}, with its test, decision rule and a 2020 sensitivity fixed in advance; the Stage B protocol, carrying the hash of the hypothesis file, at {CT['Stage B protocol'][11:16]}; and the Stage B analysis at {CT['Stage B results'][11:16]}. These are local commit times; the commits are now in the public repository, but their push time is not recorded in the commit history, so the order rests on the author's commit history rather than an external timestamp. Stage A is therefore exploratory, and Stage B is a registered follow-up test on data that were public but not yet evaluated.

## 5. Results

### 5.1 Two event years with all six models

Table 2 gives the next-day comparison on the 528 festival-window cases of 2024–2025, and Figure 1 all leads. Festival information helps the local models: typed and pooled day flags lower Rich Ridge event MASE from 0.57699 to 0.45317 and 0.46093, and SARIMAX from 0.57301 to 0.42533 and 0.45345. Chronos-2 gains little; TimesFM-3 gains with both day flags (typed 0.48005, pooled 0.42459, against 0.55148 for calendar). Window indicators help little. The typed-minus-pooled contrast ranges from -0.03971 to 0.05564 across the 36 model/representation/lead cells and its sign is opposite between 2024 and 2025 in 19 cells (supplement; lead 1 by family in Appendix Table A4). Across the 36 cells, {N['T1_raw']} reach a raw sign-flip p below 0.05, against {N['expected_raw']} expected if every null were true; the smallest raw p is {N['T1_min']} (TimesFM-3 day flags). With 10 clusters no ordering can be confirmed (Appendix Table A13). On ordinary days (Appendix Table A1) the arms differ less, but for both foundation models the day arms slightly raise ordinary-day MASE. Zero-channel and placebo controls for this cohort are in Appendix Table A14; pure daily calendar encodings for the foundation models, fixed response-profile comparators and support/heterogeneity diagnostics are in Appendix Tables A6, A3 and A5.

Table 2. 2024–2025 festival windows (document-aligned, recentered): lead-1 MASE.

{table('Table 1')}

![Figure 1. Typed minus pooled MASE on the same 2024–2025 festival-window cases, all models, representations and leads. Positive values favour pooling.](figures/india_contrasts.png)

### 5.2 Stage A: four event years

Two earlier event years (2022–2023) were added after the 2020–2021 calendars needed as their training history had been checked; this doubles the event cases to {sad['event_cases']:,} and the clusters to {sad['family_year_clusters']}. Parameters for the new years were selected by the unchanged pre-year procedure, and re-running the 2024–2025 subset reproduced the stored local forecasts (maximum difference 1.4 × 10^-13). Table 3 gives the lead-1 contrasts.

One cell passes the pre-set rule (Holm p below 0.05 and the same sign in at least three of four years): Stable LightGBM is better with the pooled day flag ({s4(SAN['lgb']['typed_minus_pooled'])}, Holm p {float(SAN['lgb']['holm_primary']):.3f}; 2024 is an exact tie). The leaf-2 LightGBM points the same way in all four years ({s4(SAN['lgb2']['typed_minus_pooled'])}, Holm p {float(SAN['lgb2']['holm_primary']):.3f}), and SARIMAX points the other way in all four years ({s4(SAN['sar']['typed_minus_pooled'])}, raw p {float(SAN['sar']['p_signflip']):.4f}, Holm p {float(SAN['sar']['holm_primary']):.3f}). Rich Ridge shows no ordering. Leaving out any one festival family does not change the sign of these three day contrasts. The window representations show no clear ordering. The LightGBM result needs care: a typed flag has at most four flagged days in a 730-day training window, fewer than the minimum of five or 20 samples per leaf that the stable LightGBM may select, so its trees cannot split on typed flags at all, whereas the pooled flag can have more than ten flagged days. Its pooling advantage may therefore reflect the number of flagged days rather than a preference for pooled information; the leaf-2 LightGBM, which can split on typed flags, still favours pooling in all four years. Over all 24 model/representation/lead cells, {raw24} have a raw p below 0.05 and none survives Holm over 24.

The controls behave as intended (Table 4): at lead 1 the zero-channel and placebo-day arms stay within {ctl_gap:.4f} of the calendar arm for every local model ({ctl_gap_w:.4f} including the window placebos), whereas typed and pooled day flags lower Rich Ridge and SARIMAX MASE by more than 0.1. The gains therefore come from the festival dates, not from extra channels.

Table 3. Stage A (2022–2025, 20 clusters): lead-1 typed minus pooled MASE, balanced over all years and by year. Positive favours pooling. LGBM: Stable LightGBM; LGBM-2: tree leaf minimum 2. Same sign: years agreeing with the all-years sign. p: exact two-sided sign-flip; Holm over the eight lead-1 cells. Typed and pooled MASE are in Table 4.

{chr(10).join(t_sa)}

Table 4. Stage A controls: lead-1 event MASE.

{chr(10).join(t_sactl)}

### 5.3 Foundation models over four years

The foundation models were extended to the Stage A years by a separately registered run (results/longer_panel_foundation_v1; protocol committed before any of its forecasts, run on a hosted CPU notebook). It first re-forecast the 2024 event cases for three reference arms: all {fs['reproduction']['rows']:,} forecasts matched the stored ones within the registered tolerance (largest difference {fs['reproduction']['max_abs_difference']:.5f} GWh), so the new 2022–2023 forecasts were combined with the stored 2024–2025 ones. This analysis is exploratory: the registered model-class hypothesis concerns the local models only.

Table 5 gives the lead-1 contrasts. TimesFM-3 is better with the pooled day flag ({s4(FN['tf']['typed_minus_pooled'])}, Holm p {float(FN['tf']['holm_primary']):.3f}, all four years), which passes the Stage A rule. The two new years agree with the 2024–2025 pattern noted in the earlier version as an expectation for future confirmation ({s4(FN['tf']['year_2022'])} in 2022 and {s4(FN['tf']['year_2023'])} in 2023), although that expectation was not registered as a hypothesis. The pooled day flag lowers TimesFM-3 MASE from {f5(FN['tfc']['calendar'])} (calendar) to {f5(FN['tfc']['pooled_day5'])}, while the typed flags give {f5(FN['tfc']['day5'])}. Chronos-2 shows no ordering ({s4(FN['ch']['typed_minus_pooled'])}, raw p {float(FN['ch']['p_signflip']):.4f}) and gains little from either flag. The zero-channel and placebo arms stay within {f_gap:.4f} of calendar for both models. Unlike the stable LightGBM, TimesFM-3 receives the flags as input channels and can in principle use typed flags, so its preference for pooling is not explained by a minimum leaf size.

Table 5. Foundation models over Stage A (2022–2025, 20 clusters): lead-1 MASE and typed minus pooled contrast. Positive favours pooling. Holm over the four lead-1 cells. 2022–2023 forecasts from the registered extension; 2024–2025 from the stored runs.

{chr(10).join(t_fd)}

### 5.4 Stage B: registered test on further years

Because the model-class pattern was found in the Stage A data, it was stated as a hypothesis before any new test data were used: H1, Stable LightGBM favours the pooled day flag; H2, SARIMAX favours typed day flags; H1b (secondary), the same as H1 for the leaf-2 LightGBM; H3, Ridge, reported only. The test data are Maharashtra event years 2019–2021, which had not been evaluated as targets by any model or arm; their 2020–2021 values were, however, training history for the 2022–2023 Stage A models, and Maharashtra is one of the Stage A states. Calendars for 2017–2021 were checked by hand ({sbd['event_cases']} cases, {sbd['clusters']} clusters, no missing labels). The decision rule was fixed in advance: one-sided exact sign-flip p over 15 clusters, Holm across H1 and H2, and the sign must hold in at least two of three years; the COVID year 2020 is removed as a pre-declared sensitivity.

Table 6 gives the result. H2 is confirmed ({SB_N['h2']}, one-sided p {SB_N['h2p']}, Holm p {SB_N['h2h']}, all three years) and still holds without 2020 ({SB_N['h2s']}, Holm p {SB_N['h2sh']}). H1 is exactly zero, which makes the test uninformative rather than evidence against H1: for lead 1 the pre-year selection chose a minimum of 20 samples per leaf in all three years, while the pooled flag is set on at most 13 and a typed flag on at most four of the 730 training days, so no tree splits on any festival column and every arm gives the same forecast (balanced MASE {SB_N['lgb']} for all five arms, Table 7). The same mechanism explains the exact tie in Stage A's 2024. It could have been anticipated from that tie but was not written into the registration, so the registered decision stands. The leaf-2 LightGBM, whose trees can use the flags, favours pooling ({SB_N['h1b']}, unadjusted one-sided p {SB_N['h1bp']}, two of three years; 2019 has the opposite sign); the registration fixed a decision rule only for H1 and H2, so this secondary result is descriptive, and it does not hold without 2020 ({SB_N['h1bs']}, p {SB_N['h1bsp']}). Rich Ridge favours typed flags in Maharashtra ({SB_N['ridge']}), unlike Stage A. Figure 2 shows the yearly contrasts across both stages.

Table 6. Stage B (Maharashtra 2019–2021, 15 clusters): registered hypothesis tests at lead 1 (day flags), typed minus pooled MASE. H1 and H1b expect a positive value (pooling better), H2 a negative one. H1b is secondary and not Holm-adjusted. Decision rule: Holm p below 0.05 and the expected sign in at least two of three years.

{chr(10).join(t_sb)}

Table 7. Stage B controls: lead-1 event MASE (Maharashtra 2019–2021).

{chr(10).join(t_sbctl)}

![Figure 2. Lead-1 typed minus pooled MASE (day flags) by year for the local models. Positive values favour pooling. Stage B uses Maharashtra only; Stage A averages three states.](figures/per_year.png)

### 5.5 Closest-method comparators

Ziel's designs (Table 8) improve on the calendar baseline in all 12 Indian local model/lead cells for each design in 2024–2025, but the additive typed and pooled day flags also do so in 22 of their 24 cells, and the replacing designs differ consistently from the additive flags they carry in only 3 (Rph) and 4 (RpH) of 12 cells. For SARIMAX and Rich Ridge the typed replacing design (RpH) has the lowest lead-1 MASE among the arms in Table 8, which agrees with the SARIMAX preference for typed flags. In NYC event windows hSun raises MASE relative to calendar in all 12 local cells, and Rph and RpH in 9 and 6 of 12 (Appendix Tables A7 and A8).

Table 8. Ziel adaptations on Indian festival windows (2024–2025): local-model lead-1 MASE. The first three columns equal Table 2.

{table('Table A6')}

### 5.6 NYC replication

Table 9 repeats the main comparison on NYC. Within NYC, 36 of 144 family/mode/step cells favour pooling, 96 favour separate identities and 12 tie. India (2024–2025) and NYC agree in sign in 22 of 36 cells, are opposite in 11 and tie in 3. SARIMAX typed-day flags improve on calendar while pooled-day flags worsen it, consistent with the Indian SARIMAX result, whereas pooling helps the NYC ordinary sample (Appendix Table A2); Rich Ridge also prefers typed flags in NYC, while Chronos-2 prefers pooled.

Table 9. NYC event windows: decision lead 1 (model step 8), MASE.

{table('Table 4')}

## 6. What should a forecaster do?

If the better representation is uncertain, choosing it from past performance may not help. Using stored forecasts only, we compare always-typed, always-pooled, an equal-weight average of the typed and pooled point forecasts, and a rule that uses each year whichever representation had the lower balanced MASE in the previous year. Regret is MASE minus that of the better representation in hindsight for the same cell; it can be negative for the average. The rules were chosen after the instability had been observed, so this analysis is exploratory.

Over the {sa['decision_cells']} Stage A decision cells (four local models, two representations, three leads, three years with a previous year), following last year's winner picks the worse representation in {sa['follow_picked_worse']} cells. Mean regret is {mr['follow']:.4f} for the follow rule, {mr['typed']:.4f} for always-typed, {mr['pooled']:.4f} for always-pooled and {mr['average']:.4f} for the average; the largest regret is {xr['follow']:.3f}, {xr['typed']:.3f}, {xr['pooled']:.3f} and {xr['average']:.3f} respectively (Table 10). The follow rule is not useless: its mean regret is below that of either fixed choice; but it picks the worse representation in {sa['follow_picked_worse']} of {sa['decision_cells']} cells and has the same worst case as always-typed. No test was run on these differences. For the 2024–2025 cohort with all six models and for NYC (all cells and leads; lead 1 in Appendix Tables A11 and A12), the largest regret of the average is below that of both fixed choices (India {N['xc_i']} against {N['xt_i']} and {N['xp_i']}; NYC {N['xc_n']} against {N['xt_n']} and {N['xp_n']}, only narrowly), while in NYC always-typed has the lower mean regret ({N['mt_n']} against {N['mc_n']}).

By construction, the absolute error of an equal-weight average is at most the mean of the two absolute errors, so the average cannot be worse than the worse representation; its advantage is in limiting the worst case, it is not shown to improve typical accuracy, and it is not a new method. Combined with the model-class result, a cautious reading is: typed flags suit SARIMAX; TimesFM-3 did better with a pooled flag; tree models can use rare flags only if their minimum leaf size allows it, and then did better with a pooled flag; and the average is a safe default when the choice is unclear.

Table 10. Stage A decision rules over {sa['decision_cells']} cells (regret in MASE relative to the hindsight-better representation).

| Rule | Mean regret | Largest regret |
| --- | --- | --- |
| Always typed | {mr['typed']:.4f} | {xr['typed']:.3f} |
| Always pooled | {mr['pooled']:.4f} | {xr['pooled']:.3f} |
| Follow last year's winner | {mr['follow']:.4f} | {xr['follow']:.3f} |
| Average of typed and pooled | {mr['average']:.4f} | {xr['average']:.3f} |

## 7. Uncertainty and reproducibility

Both foundation models are compared on their native quantiles 0.1–0.9 for 2024–2025 (Appendix Table A9); family/year coverage of the nominal 80% interval falls below 0.80 in 85 of 100 cluster/arm cells (Appendix Table A10). The NESO delay check is in Appendix Table A15. Complete clean-environment reruns of all 5,952 direct-comparator forecasts and 2,560 simulation cells are byte-identical, and Stage A reproduced the stored 2024–2025 local forecasts to 1.4 × 10^-13. These are internal software checks, not independent review. Failures are retained with notes next to the results: in Stage B, one parameter-selection run stopped at import after an environment reset, a second could not write its final log because of a relative path (its integrity check had passed and all 16 protected inputs were re-checked), and two workers did not start on the first launch; none changed a forecast.

**Frozen prospective forecasts.** Two forecast episodes were frozen before their targets existed and scored afterwards with the first complete actual vintage (retrieved {col1['retrieved_utc'][:10]}), without retuning: episode 1 was issued on {fz1['issued_utc'][:10]} for 31 October–11 November 2026 (leads 3–14, three states), and episode 2, a Chronos-2 competitor, on {fz2['issued_utc'][:10]} UTC for 1–11 November; episode 2 was observed on the public repository before its first target day. The scorer checks that the forecast file is byte-identical to the original freeze commit. Both episodes use ordinary calendar features only, so they do not test typed versus pooled festival flags, and the window contains Diwali 2026, which none of the models was given. All forecasts have MASE above 1 on this window (episode 1: {PRO['lo1']:.3f} to {PRO['hi1']:.3f}), but every forecasting model beats the last-value and weekly-repeat baselines; Chronos-2 with calendar features has the lowest error in episode 2 (Table 11). The TimesFM-3 80% intervals cover {PRO['cov_lo']:.2f} to {PRO['cov_hi']:.2f} of the 36 targets across its two arms and three interval calibrations. These are single 12-day episodes on one shared source, so no ranking or significance claim is made.

Table 11. Frozen prospective episodes: MASE on all eligible targets (three states). Both episodes use the same forecast origin (29 October); episode 2 adds Chronos-2, and its other rows are the episode-1 forecasts restricted to the episode-2 targets.

{chr(10).join(t_pro)}

## 8. Limitations

The evidence covers three states, five festival families and a few hundred festival days. Stage B uses one state that was also part of Stage A, its 2020–2021 values were Stage A training history, and its 15 clusters give limited power; the SARIMAX result is not yet shown for Delhi or Karnataka or for event years evaluated only after registration. The LightGBM hypothesis could not be tested in Stage B, the cause was visible in Stage A, and the LightGBM pooling advantage may reflect flag counts rather than representation. The registration order rests on local commit history (Section 4.4). The foundation-model results for 2022–2023 come from a hosted notebook with Python 3.13; they reproduced the stored 2024 forecasts within tolerance but not bit for bit, and the TimesFM-3 pooling preference was not registered as a hypothesis. Weather, supply constraints, coincident observances, source revisions and calendar amendments are alternative explanations; local models are refitted monthly and foundation models are frozen; weight dates do not rule out correlated pretraining exposure [5]. The decision-rule analysis is retrospective and covers only simple rules. The reuse terms of the electricity compilation are unresolved.

## 9. Conclusion

Festival day flags clearly improve Ridge and SARIMAX over a plain calendar, beyond what zero or placebo channels give. Whether typed or pooled flags are better depends on the model class. SARIMAX prefers typed flags, and this held on three further event years under a test committed to the repository beforehand. TimesFM-3 also did better with a pooled flag over four years, a pattern that a registered test on future years could check. Tree models did better with a pooled flag, but they can use a flag only if it has more flagged days than their minimum leaf size; with the larger minimum leaf size selected in Stage B they ignored festival flags altogether. A forecaster who cannot tell in advance which representation will win can average the two forecasts to limit the worst case. Testing the tree-model hypothesis needs a registered design in which the trees can use the flags.

## Declarations

**Data availability.** Code, protocols, forecasts, failures and audits are at https://github.com/Binay-verma/tsaf_project. The GRID-INDIA/POSOCO compilation curated by Robbie Andrew is in the repository; its reuse terms are unresolved. The MTA snapshot is an attributed minimal filtered extract. Model weights are not redistributed.

**Funding.** __________ [author to confirm].

**Competing interests.** __________ [author to confirm].

**Author contribution.** Binay Verma: __________ [author to complete, CRediT roles].

**Use of generative AI.** __________ [author to complete according to the journal's policy before submission].

## References

[1] Kreusel et al. (2026). On the Encoding of Calendar Features in Covariate-Informed Time Series Foundation Models. arXiv:2610.13676v1. https://arxiv.org/abs/2610.13676

[2] Alipour et al. Impact-driven event covariates for time-series foundation models. https://www.amazon.science/publications/impact-driven-event-covariates-for-time-series-foundation-models

[3] Sanyal, Mitra, McElroy and Roy (2017). Holiday Effects in Indian Manufacturing Series. U.S. Census Bureau RRS2017-04. https://www.census.gov/library/working-papers/2017/adrm/rrs2017-04.html

[4] Kaljevic, Arzola and Zhang (2026). Benchmarking Time Series Foundation Models for Load Forecasting Under Covariate Uncertainty. arXiv:2610.07232v1. https://arxiv.org/abs/2610.07232

[5] Meyer et al. Rethinking Evaluation in the Era of Time Series Foundation Models: (Un)known Information Leakage Challenges. arXiv:2510.13654v3. https://arxiv.org/abs/2510.13654

[6] Ansari et al. (2025). Chronos-2: From Univariate to Universal Forecasting. arXiv:2510.15821v1. https://arxiv.org/abs/2510.15821

[7] Jain and Sen (2026). TimesFM-3: A zero-shot foundation model for multivariate forecasting. Google Research. https://research.google/blog/timesfm-3-a-zero-shot-foundation-model-for-multivariate-forecasting/

[8] Romano, Patterson and Candès (2019). Conformalized Quantile Regression. arXiv:1905.03222v1. https://arxiv.org/abs/1905.03222

[9] Ziel (2018). Modeling public holidays in load forecasting: a German case study. Journal of Modern Power Systems and Clean Energy 6(2), 191–207. https://doi.org/10.1007/s40565-018-0385-5

[10] Arora and Taylor (2018). Rule-based autoregressive moving average models for forecasting load on special days: A case study for France. European Journal of Operational Research 266(1), 259–268. https://doi.org/10.1016/j.ejor.2017.08.056

[11] Bates and Granger (1969). The combination of forecasts. Operational Research Quarterly 20(4), 451–468. https://doi.org/10.1057/jors.1969.103

[12] Claeskens, Magnus, Vasnev and Wang (2016). The forecast combination puzzle: A simple theoretical explanation. International Journal of Forecasting 32(3), 754–762. https://doi.org/10.1016/j.ijforecast.2015.12.005

[13] Hyndman and Koehler (2006). Another look at measures of forecast accuracy. International Journal of Forecasting 22(4), 679–688. https://doi.org/10.1016/j.ijforecast.2006.03.001

[14] Ke et al. (2017). LightGBM: A highly efficient gradient boosting decision tree. Advances in Neural Information Processing Systems 30, 3146–3154.

[15] Nosek, Ebersole, DeHaven and Mellor (2018). The preregistration revolution. Proceedings of the National Academy of Sciences 115(11), 2600–2606. https://doi.org/10.1073/pnas.1708274114

[16] Holm (1979). A simple sequentially rejective multiple test procedure. Scandinavian Journal of Statistics 6(2), 65–70.

## Appendix A. Companion tables

Table A1. 2024–2025 seasonal ordinary sample: lead-1 MASE.

{table('Table 2')}

Table A2. NYC ordinary sample: decision lead 1 (model step 8), MASE.

{table('Table A1')}

Table A3. Fixed response-profile comparators on the original Indian case ledger (separate, unchanged sensitivity).

{table('Table A2')}

Table A4. 2024–2025 typed-minus-pooled MASE at lead 1 by event year and family. Positive favours pooling. LOFO: leave-one-family-out balanced contrast.

{table('Table A4')}

Table A5. Day-representation lead-1 Spearman diagnostics of past support and response heterogeneity. n counts family/state/year cells, not independent replications.

{table('Table A3')}

Table A6. Pure daily calendar encodings for the foundation models on 2024–2025 festival windows, lead-1 MASE.

{table('Table 3')}

Table A7. Ziel adaptations on NYC event windows: decision lead 1, local-model MASE.

{table('Table A8')}

Table A8. Lead-1 contrasts for the Ziel adaptations, India (top) and NYC (bottom, modes in place of years). Negative favours the first arm.

{table('Table A7')}

{table('Table A9')}

Table A9. Native 2024–2025 festival-window 80% intervals at lead 1.

{table('Table 6')}

Table A10. Native 80% coverage across the ten 2024–2025 family/year clusters at lead 1.

{table('Table A5')}

Table A11. 2024–2025, lead 1: balanced MASE over both years for typed, pooled and their average, and 2025 regret of the follow-2024 rule and of the average.

{chr(10).join(t_comb)}

Table A12. NYC, decision lead 1: balanced MASE for typed, pooled and their equal-weight average.

{chr(10).join(t_comb_n)}

Table A13. 2024–2025 typed-minus-pooled MASE at lead 1 with family-year clusters as units. The t interval is descriptive and unadjusted (df 9). Sign-flip p: exact two-sided test over 1,024 sign assignments; Holm across all 36 cells (smallest attainable {N['holm_floor36']}); year-change p: sign-flip over 5 family-level (2025 minus 2024) differences.

{chr(10).join(t_ci)}

Table A14. Controls at lead 1, 2024–2025 (India) and decision lead 1 (NYC), MASE. A dash marks an arm that was not run for that model.

{chr(10).join(t_ctl)}

Table A15. NESO calendar models at decision lead 1: ideal (model step 1) versus 21-day delay (model step 22), MASE.

{table('Table 5')}

All leads, cohorts and registered contrasts are in the supplement CSV files.
"""

# guards
used = re.findall(r"\{table\('([^']+)'\)\}", Path(__file__).read_text())
assert sorted(used) == sorted(set(used)) and len(used) == 15, used
assert md.count('[Pending') == 0
OUT.mkdir(parents=True, exist_ok=False)
shutil.copytree(V8/'figures', OUT/'figures')
per_year_figure(OUT/'figures'/'per_year')
shutil.copytree(V8/'supplement', OUT/'supplement')
for d, prefix in [(SA/'analysis', 'stage_a'), (SB/'analysis', 'stage_b'), (FD, 'foundation_stage_a')]:
    for f in sorted(d.glob('*.csv')):
        shutil.copy2(f, OUT/'supplement'/f'{prefix}_{f.name}')
(OUT/'MANUSCRIPT.md').write_text(md)
docx = OUT/'Typed_or_Pooled_Binay_Verma_v9.docx'
subprocess.run(['pandoc', str(OUT/'MANUSCRIPT.md'), '-o', str(docx), '--resource-path', str(OUT)], check=True)
subprocess.run(['soffice', '-env:UserInstallation=file:///tmp/tsfm-journal-v9-lo', '--headless', '--convert-to', 'pdf', '--outdir', str(OUT), str(docx)],
               check=True, capture_output=True)
abstract = md.split('## Abstract\n\n', 1)[1].split('\n\n', 1)[0]
json.dump(dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
               status='Journal-format draft v9 for supervisor review; not submitted; not independently reviewed beyond an internal check.',
               base={'manuscript/integrated_review_v7/MANUSCRIPT.md': sha(V7/'MANUSCRIPT.md'), 'manuscript/journal_v8/MANUSCRIPT.md': sha(V8/'MANUSCRIPT.md')},
               new_inputs={str(p.relative_to(ROOT)): sha(p) for d in (SA/'analysis', SB/'analysis', FD, P1, P2, PI) for p in sorted(d.glob('*'))} | {str(HYP.relative_to(ROOT)): sha(HYP)},
               commits=COMMITS, commit_times_utc=CT, v7_tables_copied=used, abstract_words=len(abstract.split()),
               words_main_text=len(md.split('## Declarations')[0].split()),
               outputs={p.name: sha(p) for p in [OUT/'MANUSCRIPT.md', docx]}), open(OUT/'build.json', 'w'), indent=1)
print('built', len(md.split()), 'words; abstract', len(abstract.split()))
