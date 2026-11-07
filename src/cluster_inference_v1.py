"""Registered cluster-level permutation inference for the typed-minus-pooled contrasts.

Answers reviewer question 3 (statistical unit). Inputs are the committed descriptive
cluster tables (review/journal_seven_tasks_20261031_v1/B_family_year_clusters.csv and
D_nyc_cells.csv); no forecast is re-run. Two stages, both in this file:

  python src/cluster_inference_v1.py register   # writes the protocol; commit it first
  python src/cluster_inference_v1.py analyse    # refuses unless the protocol is committed

Tests (exact enumeration, two-sided, statistic = mean of cluster values):
  T1 India, per model/representation/lead (36 cells): sign-flip over the 10 family-year
     cluster differences (1024 assignments). H0: cluster differences symmetric about 0.
  T2 India year interaction, per cell: sign-flip over the 5 family-level differences
     (2025 minus 2024) of the typed-minus-pooled value (32 assignments; minimum p 0.0625).
  T3 NYC, per model/representation/decision lead (36 cells): sign-flip over the 4
     family-mode cells (16 assignments; minimum p 0.125).
  Holm adjustment across the 36 cells within each test family. Two-sided p = share of
  assignments with |mean| >= observed |mean| (ties included, with a 1e-12 tolerance).
  Secondary, descriptive: cluster-mean t interval (95%, df = clusters - 1).
"""
import argparse
import itertools
import json
import subprocess
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from scipy import stats
from forecasting import ROOT
from festival_feature_design import sha, dump

OUT = ROOT/'results/cluster_inference_v1'
INPUTS = ['review/journal_seven_tasks_20261031_v1/B_family_year_clusters.csv',
          'review/journal_seven_tasks_20261031_v1/D_nyc_cells.csv',
          'src/cluster_inference_v1.py', 'src/test_cluster_inference_v1.py']
ALPHA = 0.05
TOL = 1e-12


def sign_flip_p(values):
    v = np.asarray(values, dtype=float)
    obs = abs(v.mean())
    signs = np.array(list(itertools.product([1., -1.], repeat=len(v))))
    means = np.abs((signs*v).mean(axis=1))
    return float(np.mean(means >= obs-TOL)), len(signs)


def holm(p):
    p = np.asarray(p, dtype=float)
    order = np.argsort(p)
    adj = np.empty_like(p)
    running = 0.
    for rank, i in enumerate(order):
        running = max(running, min(1., (len(p)-rank)*p[i]))
        adj[i] = running
    return adj


def t_interval(values):
    v = np.asarray(values, dtype=float)
    se = v.std(ddof=1)/np.sqrt(len(v))
    q = stats.t.ppf(0.975, len(v)-1)
    return v.mean()-q*se, v.mean()+q*se


def protocol():
    return dict(
        experiment=OUT.name, created_utc=datetime.now(timezone.utc).isoformat(), author='Binay Verma',
        status=('Registered before any p-value or interval was computed. The cluster values themselves were already '
                'reported descriptively (signs, ranges), so this is a pre-specified secondary analysis, not a confirmation.'),
        question='Are the typed-minus-pooled event MASE differences distinguishable from zero, and from year to year, once clusters are the unit?',
        tests=dict(T1='India: exact sign-flip on 10 family-year cluster differences per model/representation/lead (36 cells).',
                   T2='India: exact sign-flip on 5 family-level (2025 - 2024) differences per cell (year interaction).',
                   T3='NYC: exact sign-flip on 4 family-mode cell differences per model/representation/decision lead (36 cells).'),
        statistic='mean of cluster values; two-sided; ties counted with tolerance 1e-12',
        multiplicity='Holm across the 36 cells within each of T1, T2, T3; alpha 0.05',
        secondary='95% cluster-mean t interval (df = clusters - 1), descriptive only',
        interpretation=('A cell is called "detected" only if its Holm-adjusted p < 0.05. Otherwise "not detected", which is not '
                        'evidence of no difference. Minimum attainable two-sided p: T1 2/1024, T2 2/32, T3 2/16 (T2 and T3 cannot '
                        'reach 0.05 after Holm; this is reported as a power limit).'),
        assumptions=('Clusters exchangeable in sign under H0. Family-year clusters in the same year share conditions and the '
                     'NYC modes are related, so the tests are approximate; no p-value here is a confirmation.'),
        input_hashes={f: sha(ROOT/f) for f in INPUTS})


def register():
    if OUT.exists():
        raise FileExistsError('Preserve the registered protocol; create a new version')
    OUT.mkdir()
    dump(OUT/'protocol.json', protocol())


def committed(path):
    rel = str(path.relative_to(ROOT))
    r = subprocess.run(['git', 'log', '-1', '--format=%H', '--', rel], cwd=ROOT, capture_output=True, text=True)
    dirty = subprocess.run(['git', 'status', '--porcelain', '--', rel], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    return bool(r.stdout.strip()) and not dirty


def analyse():
    p = json.loads((OUT/'protocol.json').read_text())
    assert committed(OUT/'protocol.json'), 'Commit the protocol before analysing'
    for f, h in p['input_hashes'].items():
        assert sha(ROOT/f) == h, f
    if (OUT/'analysis').exists():
        raise FileExistsError('Analysis already written')
    b = pd.read_csv(ROOT/INPUTS[0]); d = pd.read_csv(ROOT/INPUTS[1])
    rows = []
    for (m, rep, lead), g in b.groupby(['model', 'representation', 'lead'], sort=False):
        assert len(g) == 10
        p1, n1 = sign_flip_p(g.typed_minus_pooled)
        w = g.pivot(index='family', columns='year', values='typed_minus_pooled')
        diff = w[2025]-w[2024]
        p2, n2 = sign_flip_p(diff)
        lo, hi = t_interval(g.typed_minus_pooled)
        rows.append(dict(source='India', model=m, representation=rep, lead=int(lead), clusters=10, mean=g.typed_minus_pooled.mean(),
                         t_low=lo, t_high=hi, p_T1=p1, assignments_T1=n1, year_change_mean=diff.mean(), p_T2=p2, assignments_T2=n2))
    india = pd.DataFrame(rows)
    india['holm_T1'] = holm(india.p_T1); india['holm_T2'] = holm(india.p_T2)
    rows = []
    for (m, rep, step), g in d.groupby(['model', 'representation', 'model_step'], sort=False):
        assert len(g) == 4
        p3, n3 = sign_flip_p(g.typed_minus_pooled)
        lo, hi = t_interval(g.typed_minus_pooled)
        rows.append(dict(source='NYC', model=m, representation=rep, decision_lead=int(step)-7, cells=4, mean=g.typed_minus_pooled.mean(),
                         t_low=lo, t_high=hi, p_T3=p3, assignments_T3=n3))
    nyc = pd.DataFrame(rows)
    nyc['holm_T3'] = holm(nyc.p_T3)
    out = OUT/'analysis'; out.mkdir()
    india.to_csv(out/'india_cluster_tests.csv', index=False); nyc.to_csv(out/'nyc_cluster_tests.csv', index=False)
    summary = dict(created_utc=datetime.now(timezone.utc).isoformat(),
                   T1=dict(cells=len(india), raw_below_005=int((india.p_T1 < ALPHA).sum()), holm_detected=int((india.holm_T1 < ALPHA).sum()),
                           min_raw_p=float(india.p_T1.min())),
                   T2=dict(cells=len(india), raw_below_005=int((india.p_T2 < ALPHA).sum()), holm_detected=int((india.holm_T2 < ALPHA).sum()),
                           min_raw_p=float(india.p_T2.min())),
                   T3=dict(cells=len(nyc), raw_below_005=int((nyc.p_T3 < ALPHA).sum()), holm_detected=int((nyc.holm_T3 < ALPHA).sum()),
                           min_raw_p=float(nyc.p_T3.min())),
                   t_interval_excludes_zero=dict(India=int(((india.t_low > 0) | (india.t_high < 0)).sum()),
                                                 NYC=int(((nyc.t_low > 0) | (nyc.t_high < 0)).sum())),
                   outputs={f.name: sha(f) for f in sorted(out.glob('*.csv'))})
    dump(out/'summary.json', summary)
    print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    a = argparse.ArgumentParser(); a.add_argument('action', choices=['register', 'analyse'])
    args = a.parse_args()
    register() if args.action == 'register' else analyse()
