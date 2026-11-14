"""Festival-level test of the heterogeneity mechanism (EXPLORATORY; after the registered analysis).

For each new state and in-scope family, estimate the festival effect (log-demand regression of
simulation_calibration_v1) and its absolute deviation from the state's mean festival effect. Then correlate
that deviation with the observed typed-minus-pooled lead-1 MASE of each model (Spearman, 27 state-family pairs):
  * same years: effects 2017-2025, outcomes 2017-2025 (partly circular)
  * out of time: effects 2015-2020, outcomes 2021-2025
The mechanism predicts a negative correlation for models that estimate one coefficient per flag.
Six models are tested, so p-values are reported unadjusted and with Bonferroni over six.
Writes results/new_states_v1_family_mechanism/.
"""
from pathlib import Path
import sys
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
import simulation_calibration_v1 as c1          # noqa: E402
import simulation_calibration_v2 as c2          # noqa: E402
import simulation_calibration_v3_timesplit as c3  # noqa: E402
import new_states_analysis_v1 as an             # noqa: E402

OUT = ROOT/'results/new_states_v1_family_mechanism'
MODELS = ['ridge', 'sarimax', 'lightgbm', 'lightgbm_capacity2', 'chronos', 'timesfm']


def effects(years):
    a = pd.read_csv(ROOT/'results/new_states_v1/anchors_2015_2025.csv')
    a = a[a.year.isin(list(years))][['state', 'family', 'year', 'date']].drop_duplicates()
    rows = []
    for st in c2.NEW:
        e = c1.estimate(*c3.frame(st, a, years))
        fams = [k[len('effect_'):] for k in e if k.startswith('effect_')]
        m = np.mean([e['effect_'+f] for f in fams])
        rows += [dict(state=st, family=f, effect=e['effect_'+f], state_mean_effect=m, deviation=abs(e['effect_'+f] - m)) for f in fams]
    return pd.DataFrame(rows)


def observed(d, model, years):
    x = d[(d.model == model) & (d.horizon == 1) & d.arm.isin(['day5', 'pooled_day5']) & d.year.isin(list(years))]
    s = x.groupby(['state', 'family', 'year', 'arm']).MASE.mean().unstack('arm')
    return (s['day5'] - s['pooled_day5']).groupby(['state', 'family']).mean().rename('typed_minus_pooled').reset_index()


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    d = an.load()
    res = []
    for label, eff_years, out_years in [('same years 2017-2025', range(2017, 2026), range(2017, 2026)),
                                        ('out of time: effects 2015-2020, outcomes 2021-2025', range(2015, 2021), range(2021, 2026))]:
        E = effects(eff_years)
        E.to_csv(OUT/f"family_effects_{eff_years.start}_{eff_years.stop - 1}.csv", index=False)
        for m in MODELS:
            j = E.merge(observed(d, m, out_years), on=['state', 'family'])
            r = stats.spearmanr(j.deviation, j.typed_minus_pooled)
            res.append(dict(design=label, model=m, pairs=len(j), spearman=r.statistic, p=r.pvalue, p_bonferroni6=min(1., 6*r.pvalue)))
    R = pd.DataFrame(res)
    R.to_csv(OUT/'spearman.csv', index=False)
    print(R.round(4).to_string(index=False))


def within():
    """Added after an internal review: within-state correlation (state means removed) and without Gujarat and Tamil Nadu."""
    d = an.load()
    rows = []
    for label, ey, oy in [('same years 2017-2025', range(2017, 2026), range(2017, 2026)), ('out of time', range(2015, 2021), range(2021, 2026))]:
        E = effects(ey)
        for m in MODELS:
            j = E.merge(observed(d, m, oy), on=['state', 'family'])
            w = j.assign(dev_w=j.deviation - j.groupby('state').deviation.transform('mean'),
                         y_w=j.typed_minus_pooled - j.groupby('state').typed_minus_pooled.transform('mean'))
            r = stats.spearmanr(w.dev_w, w.y_w)
            k = j[~j.state.isin(['Gujarat', 'Tamil Nadu'])]
            r2 = stats.spearmanr(k.deviation, k.typed_minus_pooled)
            rows.append(dict(design=label, model=m, within_state_spearman=r.statistic, within_p=r.pvalue,
                             without_GJ_TN_spearman=r2.statistic, without_GJ_TN_p=r2.pvalue, pairs_without=len(k)))
    pd.DataFrame(rows).to_csv(OUT/'within_state_and_without_GJ_TN.csv', index=False)


if __name__ == '__main__':
    within() if sys.argv[1:] == ['within'] else main()
