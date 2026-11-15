"""Power for the second registered test (seven more states), from the FIRST test's forecasts only.

No forecast or outcome of the seven new states is used. The new design's cluster structure comes from the
second-test calendar: per event year, Holi in 6 states, Dussehra in 7, Diwali in 7, Ganesh Chaturthi in 1.

R1/R2: each simulated family-year cluster takes a randomly drawn first-test family-year cluster and resamples its
state differences (with replacement) to the new number of states, so within-cluster correlation is kept. Scenarios:
the first-test effect as observed, half of it, and none (size check). Decision = one-sided sign-flip p below the
Holm level AND at least 6 of 9 year means in the hypothesised direction. Holm levels shown: 0.0125 (the hypothesis
is the first to be tested against 0.05/4 only if it has the smallest p; this is the worst case) and 0.05 (best case).

M1/M2: analogues from the first test (out-of-time h from 2015-2020, Ridge 2021-2025), reported, not simulated in
detail, because seven states give too little to calibrate a power model.
Run: python src/new_states_v2_power_v1.py
"""
from pathlib import Path
import itertools
import json
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'review/new_states_v2/power'
FIRST = ROOT/'results/new_states_v1/event_window'
YEARS = list(range(2017, 2026))
NEW = {'Holi': 6, 'Dussehra': 7, 'Diwali': 7, 'Ganesh_Chaturthi': 1}
SIMS, FLIPS, SEED = 2000, 4000, 20261116


def state_diffs(model, years=YEARS):
    p = pd.read_csv(FIRST/model/'predictions.csv')
    p = p[(p.horizon == 1) & p.arm.isin(['day5', 'pooled_day5']) & p.year.isin(years)]
    p['MASE'] = (p.prediction-p.actual).abs()/p.mase_scale
    s = p.groupby(['family', 'year', 'state', 'arm']).MASE.mean().unstack('arm')
    return (s['day5']-s['pooled_day5']).rename('diff').reset_index()


def signflip_p(v, direction, rng):
    v = np.asarray(v)*direction
    signs = rng.integers(0, 2, size=(FLIPS, len(v)), dtype=np.int8)*2-1
    return ((signs@v)/len(v) >= v.mean()-1e-12).sum()/FLIPS


def power(model, direction, scale, rng):
    d = state_diffs(model)
    first = d.groupby(['family', 'year'])['diff'].mean()
    effect = first.mean()
    d['diff'] = d['diff']-(1-scale)*effect          # shift so the expected cluster mean is scale*effect
    groups = [g['diff'].values for _, g in d.groupby(['family', 'year'])]
    hits = {0.0125: 0, 0.05: 0}; ps = []
    for _ in range(SIMS):
        vals, yrs = [], []
        for y in YEARS:
            for f, n in NEW.items():
                g = groups[rng.integers(len(groups))]
                vals.append(rng.choice(g, n, replace=True).mean()); yrs.append(y)
        vals = np.array(vals); yrs = np.array(yrs)
        ym = np.array([vals[yrs == y].mean() for y in YEARS])
        p = signflip_p(vals, direction, rng); ps.append(p)
        ok_years = (np.sign(ym) == direction).sum() >= 6
        for a in hits:
            hits[a] += (p < a) and ok_years
    return dict(model=model, scenario={1.0: 'first-test effect', 0.5: 'half effect', 0.0: 'no effect'}[scale],
                first_test_effect=round(float(effect), 4), first_test_clusters=len(first),
                power_holm_worst_0_0125=hits[0.0125]/SIMS, power_holm_best_0_05=hits[0.05]/SIMS, median_p=float(np.median(ps)))


def mechanism_analogue():
    cal = pd.read_csv(ROOT/'results/simulation_calibration_v3_timesplit/calibration_2015_2020.csv')
    obs = pd.read_csv(ROOT/'results/simulation_calibration_v3_timesplit/predicted_2015_2020_vs_observed_2021_2025.csv')
    r = obs[obs.model == 'ridge'][['state', 'observed_typed_minus_pooled']].merge(cal[['state', 'h']], on='state')
    rho = spearmanr(r.h, r.observed_typed_minus_pooled).statistic
    perms = [spearmanr(r.h, np.array(q)).statistic for q in itertools.permutations(r.observed_typed_minus_pooled)]
    p_m2 = float(np.mean(np.array(perms) <= rho+1e-12))
    top = r.sort_values('h', ascending=False).head(3).state.tolist()
    d = state_diffs('ridge', range(2021, 2026))
    u = d[d.state.isin(top)]['diff'].values
    rng = np.random.default_rng(SEED)
    p_m1 = signflip_p(u, -1, rng)
    # M1 power: resample state-family-year units of the top-3 first-test states, same unit count as the new top 3 would give
    hits = 0
    for _ in range(SIMS):
        hits += signflip_p(rng.choice(u, len(u), replace=True), -1, rng) < 0.0125
    return dict(first_test_h=r.set_index('state').h.round(3).to_dict(),
                first_test_ridge_2021_2025=r.set_index('state').observed_typed_minus_pooled.round(4).to_dict(),
                states_with_h_zero=int((r.h == 0).sum()),
                M2_first_test_spearman=round(float(rho), 3), M2_first_test_exact_p=round(p_m2, 4),
                M1_top3_first_test=top, M1_units=len(u), M1_mean=round(float(u.mean()), 4), M1_first_test_p=round(float(p_m1), 4),
                M1_power_bootstrap_holm_worst=hits/SIMS)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    rows = [power(m, s, k, rng) for m, s in [('sarimax', -1), ('lightgbm_capacity2', +1)] for k in (1.0, 0.5, 0.0)]
    r = pd.DataFrame(rows)
    r.insert(0, 'hypothesis', r.model.map({'sarimax': 'R1', 'lightgbm_capacity2': 'R2'}))
    r.to_csv(OUT/'power_R1_R2.csv', index=False)
    m = mechanism_analogue()
    (OUT/'mechanism_analogue.json').write_text(json.dumps(m, indent=1))
    print(r.to_string(index=False)); print(json.dumps(m, indent=1))


if __name__ == '__main__':
    main()
