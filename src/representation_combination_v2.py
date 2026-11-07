"""Version 2 (only change from v1: the NYC filter keeps local models, whose scenario label is empty).

Registered exploratory analysis: what should a forecaster do when typed-versus-pooled is unstable?

Uses only stored forecasts (no model is re-run). For each model, representation (day, window)
and lead, three pre-specified decision rules are compared with always-typed and always-pooled:

  combine     equal-weight mean of the typed and pooled point forecasts (no weights estimated)
  follow_2024 use, in 2025, whichever of typed / pooled had the lower 2024 balanced MASE
              (India only: the only setting with an earlier event year)
  oracle      the better of typed / pooled in hindsight (a bound, not a usable rule)

Metrics: balanced event MASE (the v6 hierarchy). India uses the composed document-aligned
forecasts; NYC uses the recovery forecasts (scenario lag7, decision-lead steps 8/14/21).
Regret = rule MASE minus oracle MASE. Reported counts: cells where combine beats both single
representations, beats the worse one, and its regret versus follow_2024 (India, 2025 only).
Exact sign-flip tests (cluster_inference_v1 method) of combine minus pooled and combine minus typed,
on 10 India family-year clusters or 4 NYC family-mode cells, Holm across the 36 cells of each. No test
against the per-cell better representation, because that target is chosen in hindsight.

  python src/representation_combination_v1.py register   # commit before analysing
  python src/representation_combination_v1.py analyse
"""
import argparse
import json
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from forecasting import ROOT
from festival_feature_design import sha, dump
from cluster_inference_v1 import sign_flip_p, holm, committed

OUT = ROOT/'results/representation_combination_v2'
INDIA = 'results/calendar_recenter_recovery_v1/analysis/breadth/event_window/predictions_compared.csv'
NYC = 'results/mta_holiday_recovery_v1/analysis/event_window/predictions_compared.csv'
INPUTS = [INDIA, NYC, 'src/representation_combination_v2.py', 'src/cluster_inference_v1.py', 'src/test_representation_combination_v1.py',
          'results/representation_combination_v1/NOTE_NYC_FILTER.md']
MODELS = ['ridge', 'sarimax', 'lightgbm', 'lightgbm_capacity2', 'chronos', 'timesfm']
REPS = {'day': ('day5', 'pooled_day5'), 'window': ('window5', 'pooled_window5')}


def register():
    if OUT.exists():
        raise FileExistsError('Preserve the registered protocol')
    OUT.mkdir()
    dump(OUT/'protocol.json', dict(experiment=OUT.name, created_utc=datetime.now(timezone.utc).isoformat(), author='Binay Verma',
        status=('Exploratory. Corrects the v1 NYC filter, which dropped the four local models. v1 India results and the v1 NYC foundation-model '
                'results were already computed; the NYC local-model combination results were not.'),
        rules=['typed', 'pooled', 'combine (equal-weight mean of typed and pooled point forecasts)',
               'follow_2024 (India 2025 only)', 'oracle (hindsight bound)'],
        metrics='balanced event MASE; regret versus oracle; counts of cells; sign-flip on 10 India family-year clusters / 4 NYC family-mode cells with Holm across 36 cells',
        interpretation='Descriptive. "Combination helps" may be said only of cells where combine is below both single representations; no claim of general superiority.',
        input_hashes={f: sha(ROOT/f) for f in INPUTS}))


def frame(path, india):
    d = pd.read_csv(ROOT/path)
    if india:
        d = d[d.version.eq('document_aligned')]
    else:
        d = d[d.scenario.eq('lag7') | d.scenario.isna()]  # v2 fix: local models carry no scenario label
    d = d[d.model.isin(MODELS)]
    key = ['model', 'family', 'state', 'year', 'date', 'origin', 'horizon']
    out = []
    for rep, (t, p) in REPS.items():
        a = d[d.arm.eq(t)].set_index(key); b = d[d.arm.eq(p)].set_index(key)
        assert a.index.equals(b.index.sort_values()) or set(a.index) == set(b.index)
        b = b.reindex(a.index)
        assert np.allclose(a.actual, b.actual) and np.allclose(a.mase_scale, b.mase_scale)
        x = pd.DataFrame(index=a.index)
        x['typed'] = (a.prediction-a.actual).abs()/a.mase_scale
        x['pooled'] = (b.prediction-b.actual).abs()/b.mase_scale
        x['combine'] = ((a.prediction+b.prediction)/2-a.actual).abs()/a.mase_scale
        x['representation'] = rep
        out.append(x.reset_index())
    return pd.concat(out, ignore_index=True)


def cluster_values(x, col, keep_state=False):
    """India: family-year clusters (states averaged). NYC: family-mode cells (keep_state=True)."""
    s = x.groupby(['model', 'representation', 'horizon', 'family', 'year', 'state'])[col].mean()
    return s if keep_state else s.groupby(['model', 'representation', 'horizon', 'family', 'year']).mean()


def balanced(x, col):
    c = cluster_values(x, col)
    return c.groupby(['model', 'representation', 'horizon', 'family']).mean().groupby(['model', 'representation', 'horizon']).mean()


def analyse():
    assert committed(OUT/'protocol.json'), 'Commit the protocol first'
    p = json.loads((OUT/'protocol.json').read_text())
    for f, h in p['input_hashes'].items():
        assert sha(ROOT/f) == h, f
    if (OUT/'analysis').exists():
        raise FileExistsError('Analysis already written')
    results = {}
    out = OUT/'analysis'; out.mkdir()
    for source, path, india in [('India', INDIA, True), ('NYC', NYC, False)]:
        x = frame(path, india)
        b = pd.DataFrame({c: balanced(x, c) for c in ['typed', 'pooled', 'combine']})
        b['oracle'] = b[['typed', 'pooled']].min(axis=1)
        b['combine_below_both'] = b["combine"] < b.oracle
        b['combine_below_worse'] = b["combine"] < b[['typed', 'pooled']].max(axis=1)
        b['combine_regret'] = b["combine"]-b.oracle
        if india:
            y24 = pd.DataFrame({c: balanced(x[x.year.eq(2024)], c) for c in ['typed', 'pooled', 'combine']})
            y25 = pd.DataFrame({c: balanced(x[x.year.eq(2025)], c) for c in ['typed', 'pooled', 'combine']})
            choice = np.where(y24.typed < y24.pooled, 'typed', 'pooled')
            y25['follow_2024'] = [y25.loc[i, c] for i, c in zip(y25.index, choice)]
            y25['oracle'] = y25[['typed', 'pooled']].min(axis=1)
            y25['follow_regret'] = y25.follow_2024-y25.oracle
            y25['combine_regret'] = y25["combine"]-y25.oracle
            y25['follow_picked_worse'] = y25.follow_regret > 0
            y25.reset_index().to_csv(out/'india_2025_decision_rules.csv', index=False)
        ps = {}
        for ref in ['typed', 'pooled']:
            diff = cluster_values(x, 'combine', not india)-cluster_values(x, ref, not india)
            raw = diff.groupby(['model', 'representation', 'horizon']).apply(lambda v: sign_flip_p(v.values)[0])
            ps[ref] = pd.DataFrame({'p': raw, 'holm': holm(raw.values)}, index=raw.index)
        b['p_vs_typed'] = ps['typed'].p; b['holm_vs_typed'] = ps['typed'].holm
        b['p_vs_pooled'] = ps['pooled'].p; b['holm_vs_pooled'] = ps['pooled'].holm
        b.reset_index().to_csv(out/f'{source.lower()}_combination.csv', index=False)
        r = dict(cells=len(b), combine_below_both=int(b["combine_below_both"].sum()), combine_below_worse=int(b["combine_below_worse"].sum()),
                 mean_combine_regret=float(b["combine_regret"].mean()), max_combine_regret=float(b["combine_regret"].max()),
                 mean_abs_typed_minus_pooled=float((b.typed-b.pooled).abs().mean()),
                 holm_detected_vs_typed=int((b.holm_vs_typed < 0.05).sum()), holm_detected_vs_pooled=int((b.holm_vs_pooled < 0.05).sum()))
        if india:
            r['india_2025'] = dict(cells=len(y25), follow_picked_worse=int(y25.follow_picked_worse.sum()),
                                   mean_follow_regret=float(y25.follow_regret.mean()), mean_combine_regret=float(y25["combine_regret"].mean()),
                                   combine_beats_follow=int((y25["combine"] < y25.follow_2024).sum()))
        results[source] = r
    results['created_utc'] = datetime.now(timezone.utc).isoformat()
    results['outputs'] = {f.name: sha(f) for f in sorted(out.glob('*.csv'))}
    dump(out/'summary.json', results)
    print(json.dumps(results, indent=1))


if __name__ == '__main__':
    a = argparse.ArgumentParser(); a.add_argument('action', choices=['register', 'analyse'])
    args = a.parse_args()
    register() if args.action == 'register' else analyse()
