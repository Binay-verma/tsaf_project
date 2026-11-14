"""Exploratory diagnostics for the registered new-states analysis (written after it; not confirmatory).

Uses the registered functions (load, clusters, signflip) unchanged and the same 45 family-year clusters.
  1. leave-one-state-out and leave-one-year-out: H1-H3 effect and one-sided p (100k draws each)
  2. horizons 1, 7 and 14 for every model (lead 1 is the registered horizon)
  3. effect sizes in physical units: typed-minus-pooled absolute error in GWh and as % of actual demand
  4. power: minimum detectable effect at 80% power for 45 clusters, given the observed cluster spread
  5. typed and pooled against the zero-flag and placebo controls (local models)
Writes results/new_states_v1_diagnostics/.
"""
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
import new_states_analysis_v1 as an  # noqa: E402

OUT = ROOT/'results/new_states_v1_diagnostics'
DRAWS = 100_000


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    d = an.load()
    d['abs_err'] = (d.prediction - d.actual).abs()
    d['pct_err'] = 100*d.abs_err/d.actual
    keys = d[['state', 'family', 'year']].drop_duplicates()
    rows = []
    for h, (m, direction) in an.HYP.items():
        full = an.clusters(d, m)
        rows.append(dict(hypothesis=h, model=m, left_out='none', clusters=len(full), effect=full.mean(),
                         p_one_sided=an.signflip(full.values, direction, DRAWS)))
        for st in sorted(d.state.unique()):
            c = an.clusters(d, m, keep=keys[keys.state != st])
            rows.append(dict(hypothesis=h, model=m, left_out=f'state: {st}', clusters=len(c), effect=c.mean(),
                             p_one_sided=an.signflip(c.values, direction, DRAWS)))
        for y in an.EVENT_YEARS:
            c = an.clusters(d, m, [x for x in an.EVENT_YEARS if x != y])
            rows.append(dict(hypothesis=h, model=m, left_out=f'year: {y}', clusters=len(c), effect=c.mean(),
                             p_one_sided=an.signflip(c.values, direction, DRAWS)))
    loo = pd.DataFrame(rows)
    loo['direction_kept'] = np.sign(loo.effect) == loo.hypothesis.map({k: v[1] for k, v in an.HYP.items()})
    loo.to_csv(OUT/'leave_one_out.csv', index=False)

    hz = []
    for m in sorted(d.model.unique()):
        for hor in sorted(d.horizon.unique()):
            x = d[(d.model == m) & (d.horizon == hor) & d.arm.isin(['day5', 'pooled_day5'])]
            s = x.groupby(['family', 'year', 'state', 'arm']).MASE.mean().unstack('arm')
            c = (s['day5'] - s['pooled_day5']).groupby(['family', 'year']).mean()
            hz.append(dict(model=m, horizon=hor, typed_minus_pooled=c.mean(), clusters=len(c),
                           p_two_sided=min(1, 2*min(an.signflip(c.values, 1, DRAWS), an.signflip(c.values, -1, DRAWS)))))
    pd.DataFrame(hz).to_csv(OUT/'by_horizon.csv', index=False)

    phys = []
    for m in sorted(d.model.unique()):
        x = d[(d.model == m) & (d.horizon == 1) & d.arm.isin(['day5', 'pooled_day5'])]
        g = x.groupby(['family', 'year', 'state', 'arm'])[['abs_err', 'pct_err', 'actual']].mean().unstack('arm')
        de = (g['abs_err']['day5'] - g['abs_err']['pooled_day5']).groupby(['family', 'year']).mean()
        dp = (g['pct_err']['day5'] - g['pct_err']['pooled_day5']).groupby(['family', 'year']).mean()
        base = g['pct_err']['pooled_day5'].groupby(['family', 'year']).mean()
        phys.append(dict(model=m, typed_minus_pooled_GWh=de.mean(), typed_minus_pooled_pct_points=dp.mean(),
                         pooled_mean_abs_pct_error=base.mean(), mean_actual_GWh=g['actual']['day5'].mean()))
    pd.DataFrame(phys).to_csv(OUT/'physical_units.csv', index=False)

    pw = []
    z = stats.norm.ppf(0.95) + stats.norm.ppf(0.80)
    for h, (m, direction) in an.HYP.items():
        c = an.clusters(d, m)
        sd = c.std(ddof=1)
        pw.append(dict(hypothesis=h, model=m, clusters=len(c), cluster_sd=sd, observed_effect=c.mean(),
                       mde_80pct_one_sided_alpha05=z*sd/np.sqrt(len(c)),
                       mde_80pct_holm_worst_alpha0167=(stats.norm.ppf(1-0.05/3) + stats.norm.ppf(0.80))*sd/np.sqrt(len(c))))
    pd.DataFrame(pw).to_csv(OUT/'power.csv', index=False)

    ctl = []
    for m in ['ridge', 'lightgbm', 'lightgbm_capacity2', 'sarimax']:
        x = d[(d.model == m) & (d.horizon == 1)]
        s = x.groupby(['family', 'year', 'state', 'arm']).MASE.mean().unstack('arm').groupby(['family', 'year']).mean()
        for a in ['day5', 'pooled_day5', 'placebo_day5']:
            c = s[a] - s['zero5']
            ctl.append(dict(model=m, arm=a, minus_zero5=c.mean(),
                            p_two_sided=min(1, 2*min(an.signflip(c.values, 1, DRAWS), an.signflip(c.values, -1, DRAWS)))))
    pd.DataFrame(ctl).to_csv(OUT/'against_controls.csv', index=False)

    summary = dict(note='Exploratory diagnostics after the registered analysis; registered decisions unchanged.',
                   leave_one_out_direction_kept={h: f"{int(loo[(loo.hypothesis == h) & (loo.left_out != 'none')].direction_kept.sum())}/"
                                                    f"{int((loo[(loo.hypothesis == h) & (loo.left_out != 'none')]).shape[0])}" for h in an.HYP},
                   leave_one_out_p_below_05={h: f"{int((loo[(loo.hypothesis == h) & (loo.left_out != 'none')].p_one_sided < .05).sum())}/"
                                                f"{int((loo[(loo.hypothesis == h) & (loo.left_out != 'none')]).shape[0])}" for h in an.HYP})
    (OUT/'summary.json').write_text(json.dumps(summary, indent=1))
    for f in ['leave_one_out', 'by_horizon', 'physical_units', 'power', 'against_controls']:
        print(f); print(pd.read_csv(OUT/f'{f}.csv').round(4).to_string(index=False))
    print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    main()
