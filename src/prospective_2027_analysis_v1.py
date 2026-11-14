"""Analysis for the prospective 2027-2028 test (results/prospective_2027_v1/REGISTRATION_DRAFT.md).

Written before any 2027 data exists. Input: a predictions table with the registered columns
(family,state,year,date,horizon,origin,actual,prediction,mase_scale,model,arm) for event years 2027-2028.
Run: python src/prospective_2027_analysis_v1.py PREDICTIONS.csv [PREDICTIONS2.csv ...]
Writes results/prospective_2027_v1/analysis/ (refuses to overwrite).
"""
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'results/prospective_2027_v1'
TYPED_STATES = ['Rajasthan', 'Gujarat', 'Tamil Nadu']
POOLED_STATES = ['Uttar Pradesh', 'Madhya Pradesh', 'Telangana', 'Andhra Pradesh']
YEARS = [2027, 2028]
DRAWS, SEED, ALPHA = 1_000_000, 20271101, 0.05
PRIMARY = {'P1': ('ridge', [1], TYPED_STATES), 'P2': ('timesfm', [7, 14], TYPED_STATES)}
SECONDARY = {'S1_sarimax_typed_states': ('sarimax', [1], TYPED_STATES),
             'S2_ridge_pooled_states': ('ridge', [1], POOLED_STATES),
             'S3_timesfm_pooled_states': ('timesfm', [7, 14], POOLED_STATES)}


def signflip(v, draws=DRAWS, seed=SEED):
    """One-sided p that the mean is below zero (typed better): p = (k+1)/(N+1)."""
    v = -np.asarray(v, float)
    rng = np.random.default_rng(seed)
    obs, k = v.mean(), 0
    for start in range(0, draws, 100_000):
        n = min(100_000, draws - start)
        s = rng.integers(0, 2, size=(n, len(v)), dtype=np.int8)*2 - 1
        k += int(((s@v)/len(v) >= obs - 1e-12).sum())
    return (k + 1)/(draws + 1)


def holm(p):
    p = np.asarray(p, float); order = np.argsort(p); out = np.empty_like(p); run = 0.
    for i, j in enumerate(order):
        run = max(run, min(1., (len(p) - i)*p[j])); out[j] = run
    return out


def units(d, model, horizons, states, years=YEARS):
    """State-family-year typed minus pooled MASE, averaged over the given horizons."""
    x = d[(d.model == model) & d.horizon.isin(horizons) & d.state.isin(states) & d.year.isin(years) & d.arm.isin(['day5', 'pooled_day5'])]
    s = x.groupby(['state', 'family', 'year', 'arm']).MASE.mean().unstack('arm')
    return (s['day5'] - s['pooled_day5']).dropna()


def test(u):
    return dict(units=len(u), typed_minus_pooled=float(u.mean()), p_typed_better=signflip(u.values) if len(u) else np.nan,
                p_pooled_better=signflip(-u.values) if len(u) else np.nan)


def evaluate(d, years=YEARS):
    rows = []
    for name, (m, hz, st) in {**PRIMARY, **SECONDARY}.items():
        u = units(d, m, hz, st, years)
        rows.append(dict(test=name, model=m, horizons=str(hz), states=';'.join(st), **test(u)))
    r = pd.DataFrame(rows)
    prim = r.test.isin(PRIMARY)
    r.loc[prim, 'holm'] = holm(r.loc[prim, 'p_typed_better'].values)

    def decide(x):
        if x.test not in PRIMARY:
            return 'secondary'
        if x.typed_minus_pooled > 0 and x.p_pooled_better < ALPHA:
            return 'CONTRADICTED'
        return 'CONFIRMED' if (x.holm < ALPHA and x.typed_minus_pooled < 0) else 'NOT CONFIRMED'
    r['decision'] = r.apply(decide, axis=1)
    return r


def main(paths):
    out = OUT/'analysis'
    if out.exists():
        raise FileExistsError('analysis already written')
    d = pd.concat([pd.read_csv(p) for p in paths], ignore_index=True)
    d['MASE'] = (d.prediction - d.actual).abs()/d.mase_scale
    main_r = evaluate(d)
    interim = evaluate(d, [2027])
    out.mkdir(parents=True)
    main_r.to_csv(out/'tests.csv', index=False)
    interim.to_csv(out/'interim_2027_only_descriptive.csv', index=False)
    (out/'summary.json').write_text(json.dumps({r.test: r.decision for r in main_r.itertuples()}, indent=1))
    print(main_r.round(4).to_string(index=False))


if __name__ == '__main__':
    main(sys.argv[1:])
