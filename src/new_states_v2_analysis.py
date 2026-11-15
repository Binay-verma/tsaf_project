"""Registered confirmatory analysis for the second test, results/new_states_v2 (written before any forecast).

Run once after the four local workers finish: python src/new_states_v2_analysis.py
Writes only results/new_states_v2/analysis/. Hypotheses R1, R2, M1, M2; Holm across the four.
"""
import itertools
import json
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import rankdata
from festival_feature_design import sha, dump
from cluster_inference_v1 import holm

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'results/new_states_v2'
FIRST = ROOT/'results/new_states_v1'
H_FILE = ROOT/'review/new_states_v2/power/early_heterogeneity_2015_2020.csv'
CAL = ROOT/'review/new_states_v2/calendar_entries_2015_2025.csv'
LOCAL = ['ridge', 'lightgbm', 'lightgbm_capacity2', 'sarimax']
CLUSTER_HYP = {'R1': ('sarimax', -1), 'R2': ('lightgbm_capacity2', +1)}
M1_STATES = ['Chhattisgarh', 'West Bengal', 'Haryana']
DRAWS, SEED, ALPHA = 1_000_000, 20261116, 0.05
EVENT_YEARS = list(range(2017, 2026))
LATE = [2021, 2022, 2023, 2024, 2025]


def load(base=OUT, models=LOCAL):
    parts = []
    for m in models:
        run = json.loads((base/'event_window'/m/'run.json').read_text())
        assert sha(base/'event_window'/m/'predictions.csv') == run['predictions_sha256']
        parts.append(pd.read_csv(base/'event_window'/m/'predictions.csv'))
    d = pd.concat(parts, ignore_index=True)
    d['MASE'] = (d.prediction-d.actual).abs()/d.mase_scale
    return d


def units(d, model, years=EVENT_YEARS, keep=None, states=None):
    """State-family-year values of typed-day minus pooled-day lead-1 MASE."""
    x = d[(d.model == model) & (d.horizon == 1) & d.year.isin(years) & d.arm.isin(['day5', 'pooled_day5'])]
    if states is not None:
        x = x[x.state.isin(states)]
    if keep is not None:
        x = x.merge(keep, on=['state', 'family', 'year'])
    s = x.groupby(['family', 'year', 'state', 'arm']).MASE.mean().unstack('arm')
    return (s['day5']-s['pooled_day5']).rename('diff')


def clusters(d, model, years=EVENT_YEARS, keep=None):
    return units(d, model, years, keep).groupby(['family', 'year']).mean()


def signflip(v, direction, draws=DRAWS, seed=SEED):
    v = np.asarray(v, float)*direction
    rng = np.random.default_rng(seed)
    obs = v.mean(); k = 0
    for start in range(0, draws, 100_000):
        n = min(100_000, draws-start)
        signs = rng.integers(0, 2, size=(n, len(v)), dtype=np.int8)*2-1
        k += int(((signs@v)/len(v) >= obs-1e-12).sum())
    return (k+1)/(draws+1)


def spearman(x, y):
    rx, ry = rankdata(x), rankdata(y)
    return float(np.corrcoef(rx, ry)[0, 1])


def spearman_exact(x, y):
    """Observed Spearman and exact one-sided p in both directions over all orderings of y."""
    obs = spearman(x, y)
    perms = np.array([spearman(x, q) for q in itertools.permutations(y)])
    return obs, float(np.mean(perms <= obs+1e-12)), float(np.mean(perms >= obs-1e-12))


def h_values(column='h_abs'):
    h = pd.read_csv(H_FILE).set_index('state')[column]
    return h


def evaluate(d, years=EVENT_YEARS, keep=None, h_column='h_abs', m1_states=M1_STATES):
    rows = []
    for name, (m, direction) in CLUSTER_HYP.items():
        c = clusters(d, m, years, keep)
        yv = c.groupby(level='year').mean()
        need = 6 if len(years) == 9 else int(np.ceil(2*len(years)/3))
        rows.append(dict(hypothesis=name, model=m, expected_sign='+' if direction > 0 else '-', units=len(c), statistic=float(c.mean()),
                         years_in_direction=int((np.sign(yv) == direction).sum()), years=len(yv), years_needed=need,
                         p_one_sided=signflip(c.values, direction), p_opposite=signflip(c.values, -direction),
                         **{f'year_{y}': float(v) for y, v in yv.items()}))
    late = [y for y in LATE if y in years]
    u = units(d, 'ridge', late, keep, m1_states)
    yv = u.groupby(level='year').mean()
    rows.append(dict(hypothesis='M1', model='ridge', expected_sign='-', units=len(u), statistic=float(u.mean()),
                     years_in_direction=int((yv < 0).sum()), years=len(yv), years_needed=int(np.ceil(0.8*len(late))),
                     p_one_sided=signflip(u.values, -1), p_opposite=signflip(u.values, +1),
                     **{f'year_{y}': float(v) for y, v in yv.items()}))
    allu = units(d, 'ridge', late, keep)
    per_state = allu.groupby(level='state').mean()
    h = h_values(h_column).reindex(per_state.index)
    assert h.notna().all()
    rho, p_neg, p_pos = spearman_exact(h.values, per_state.values)
    rows.append(dict(hypothesis='M2', model='ridge', expected_sign='-', units=len(per_state), statistic=rho,
                     years_in_direction=np.nan, years=np.nan, years_needed=np.nan, p_one_sided=p_neg, p_opposite=p_pos,
                     **{f'state_{s}': float(v) for s, v in per_state.items()}))
    r = pd.DataFrame(rows)
    r['holm'] = holm(r.p_one_sided.values)

    def decide(x):
        direction = 1 if x.expected_sign == '+' else -1
        if np.sign(x.statistic) == -direction and x.p_opposite < ALPHA:
            return 'CONTRADICTED'
        years_ok = True if x.hypothesis == 'M2' else x.years_in_direction >= x.years_needed
        return 'CONFIRMED' if (x.holm < ALPHA and years_ok) else 'NOT CONFIRMED'
    r['decision'] = r.apply(decide, axis=1)
    return r


def combined(d2, d1):
    """Secondary: R1/R2 statistic over family-year clusters with the states of both tests (equal weight per state)."""
    rows = []
    for name, (m, direction) in CLUSTER_HYP.items():
        u = pd.concat([units(d1, m), units(d2, m)])
        c = u.groupby(['family', 'year']).mean()
        yv = c.groupby(level='year').mean()
        rows.append(dict(analysis=f'{name} combined (both tests, 14 states)', model=m, clusters=len(c), statistic=float(c.mean()),
                         years_in_direction=int((np.sign(yv) == direction).sum()), p_one_sided=signflip(c.values, direction)))
    return pd.DataFrame(rows)


def main():
    out = OUT/'analysis'
    if out.exists():
        raise FileExistsError('Analysis already written')
    d = load()
    main_r = evaluate(d)
    no_covid = evaluate(d, [y for y in EVENT_YEARS if y not in (2020, 2021)])
    cal = pd.read_csv(CAL, dtype=str).fillna('')
    person = cal[cal.checked_by.eq('Binay Verma')][['state', 'family', 'year']].assign(year=lambda x: x.year.astype(int))
    by_author = evaluate(d, keep=person)
    first_h = evaluate(d, h_column='h', m1_states=h_values('h').sort_values(ascending=False).index[:3].tolist())
    comb = combined(d, load(FIRST, ['lightgbm_capacity2', 'sarimax']))
    out.mkdir()
    main_r.to_csv(out/'hypothesis_tests.csv', index=False)
    no_covid.to_csv(out/'sensitivity_without_2020_2021.csv', index=False)
    by_author.to_csv(out/'sensitivity_author_checked_rows_only.csv', index=False)
    first_h.to_csv(out/'sensitivity_first_test_h.csv', index=False)
    comb.to_csv(out/'secondary_combined_both_tests.csv', index=False)
    rep = []
    for m in LOCAL:
        c = clusters(d, m)
        rep.append(dict(model=m, typed_minus_pooled=float(c.mean()), clusters=len(c),
                        p_two_sided=min(1, 2*min(signflip(c.values, 1), signflip(c.values, -1)))))
    pd.DataFrame(rep).to_csv(out/'all_models_lead1.csv', index=False)
    b = d.groupby(['model', 'arm', 'horizon', 'family', 'year', 'state']).MASE.mean().groupby(['model', 'arm', 'horizon', 'family', 'year']).mean() \
         .groupby(['model', 'arm', 'horizon', 'family']).mean().groupby(['model', 'arm', 'horizon']).mean()
    b.rename('MASE').reset_index().to_csv(out/'balanced.csv', index=False)
    s = dict(created_utc=datetime.now(timezone.utc).isoformat(),
             decisions={r.hypothesis: r.decision for r in main_r.itertuples()},
             sensitivity_without_2020_2021={r.hypothesis: r.decision for r in no_covid.itertuples()},
             sensitivity_author_checked_rows_only={r.hypothesis: r.decision for r in by_author.itertuples()},
             sensitivity_first_test_h={r.hypothesis: r.decision for r in first_h.itertuples()},
             outputs={f.name: sha(f) for f in sorted(out.glob('*.csv'))})
    dump(out/'summary.json', s)
    print(main_r.round(4).to_string(index=False)); print(comb.round(4).to_string(index=False)); print(json.dumps(s, indent=1))


if __name__ == '__main__':
    main()
