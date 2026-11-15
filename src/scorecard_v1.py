"""Registered-test scorecard with 95% intervals, per-state forest data and a random-effects summary (descriptive).

Recomputes, from the stored predictions, the cluster values behind every registered typed-vs-pooled hypothesis
(Stage B; first new-states test H1-H3; second test R1-R2, M1) and checks that the means equal the registered
statistics. Adds a 95% t interval over clusters (descriptive, unadjusted), per-state means with 95% t intervals
over family-years for the 14 new states, and a linear mixed model (state random intercept, family-year variance
component). Nothing registered is changed. Writes results/scorecard_v1/.
Run: python src/scorecard_v1.py
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.formula.api as smf

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'results/scorecard_v1'


def load(base, cohort, model, horizon=1):
    p = pd.read_csv(ROOT/base/cohort/model/'predictions.csv')
    p = p[(p.horizon == horizon) & p.arm.isin(['day5', 'pooled_day5'])]
    p['MASE'] = (p.prediction-p.actual).abs()/p.mase_scale
    s = p.groupby(['family', 'year', 'state', 'arm']).MASE.mean().unstack('arm')
    return (s['day5']-s['pooled_day5']).rename('diff').reset_index()


def fm(base, model):
    return pd.concat([load(base, c, model) for c in ['fm_2017_2020', 'fm_2021_2025']], ignore_index=True)


def tint(v):
    v = np.asarray(v, float); n = len(v); m = v.mean(); se = v.std(ddof=1)/np.sqrt(n)
    h = stats.t.ppf(0.975, n-1)*se
    return m, m-h, m+h


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    reg1 = pd.read_csv(ROOT/'results/new_states_v1/analysis/hypothesis_tests.csv').set_index('hypothesis')
    reg2 = pd.read_csv(ROOT/'results/new_states_v2/analysis/hypothesis_tests.csv').set_index('hypothesis')
    regb = pd.read_csv(ROOT/'results/longer_panel_stage_b_v1/analysis/hypothesis_tests.csv').set_index('hypothesis')
    units = {
        ('Stage B', 'Stable LightGBM, pooled better', 'H1'): (load('results/longer_panel_stage_b_v1', 'event_window', 'lightgbm'), regb.loc['H1'], 'typed_minus_pooled'),
        ('Stage B', 'SARIMAX, typed better', 'H2'): (load('results/longer_panel_stage_b_v1', 'event_window', 'sarimax'), regb.loc['H2'], 'typed_minus_pooled'),
        ('First test', 'SARIMAX, typed better', 'H1'): (load('results/new_states_v1', 'event_window', 'sarimax'), reg1.loc['H1'], 'typed_minus_pooled'),
        ('First test', 'TimesFM-3, pooled better', 'H2'): (fm('results/new_states_v1', 'timesfm'), reg1.loc['H2'], 'typed_minus_pooled'),
        ('First test', 'LightGBM leaf 2, pooled better', 'H3'): (load('results/new_states_v1', 'event_window', 'lightgbm_capacity2'), reg1.loc['H3'], 'typed_minus_pooled'),
        ('Second test', 'SARIMAX, typed better', 'R1'): (load('results/new_states_v2', 'event_window', 'sarimax'), reg2.loc['R1'], 'statistic'),
        ('Second test', 'LightGBM leaf 2, pooled better', 'R2'): (load('results/new_states_v2', 'event_window', 'lightgbm_capacity2'), reg2.loc['R2'], 'statistic'),
    }
    rows = []
    for (test, label, h), (u, reg, col) in units.items():
        c = u.groupby(['family', 'year'])['diff'].mean()
        assert abs(c.mean()-reg[col]) < 1e-9, (test, h, c.mean(), reg[col])
        m, lo, hi = tint(c.values)
        rows.append(dict(test=test, hypothesis=h, label=label, units=f'{len(c)} family-year clusters', estimate=m, ci_low=lo, ci_high=hi,
                         holm=reg['holm'], decision=reg['decision']))
    u = load('results/new_states_v2', 'event_window', 'ridge')
    u = u[u.year.isin(range(2021, 2026)) & u.state.isin(['Chhattisgarh', 'West Bengal', 'Haryana'])]
    assert abs(u['diff'].mean()-reg2.loc['M1', 'statistic']) < 1e-9
    m, lo, hi = tint(u['diff'].values)
    rows.append(dict(test='Second test', hypothesis='M1', label='Ridge, typed better in the three most dispersed states', units=f'{len(u)} state-family-years',
                     estimate=m, ci_low=lo, ci_high=hi, holm=reg2.loc['M1', 'holm'], decision=reg2.loc['M1', 'decision']))
    rows.append(dict(test='Second test', hypothesis='M2', label='Dispersion vs Ridge gain (Spearman)', units='7 states', estimate=reg2.loc['M2', 'statistic'],
                     ci_low=np.nan, ci_high=np.nan, holm=reg2.loc['M2', 'holm'], decision=reg2.loc['M2', 'decision']))
    sc = pd.DataFrame(rows)
    sc.to_csv(OUT/'scorecard.csv', index=False)

    # per-state forest data and mixed model, 14 new states
    forest, mixed = [], []
    for model in ['ridge', 'sarimax', 'lightgbm_capacity2', 'lightgbm']:
        u = pd.concat([load('results/new_states_v1', 'event_window', model).assign(test='First test'),
                       load('results/new_states_v2', 'event_window', model).assign(test='Second test')], ignore_index=True)
        for (test, st), g in u.groupby(['test', 'state']):
            m, lo, hi = tint(g['diff'].values)
            forest.append(dict(model=model, test=test, state=st, n=len(g), estimate=m, ci_low=lo, ci_high=hi))
        u['fy'] = u.family+'_'+u.year.astype(str); u['one'] = 1
        # crossed random effects: state and family-year (variance components in one group)
        r = smf.mixedlm('diff ~ 1', u, groups=u['one'], vc_formula={'state': '0 + C(state)', 'fy': '0 + C(fy)'}).fit(reml=True)
        ci = r.conf_int().loc['Intercept'].to_numpy()
        sd = dict(zip(r.model.exog_vc.names, np.sqrt(r.vcomp)))
        mixed.append(dict(model=model, states=u.state.nunique(), units=len(u), intercept=r.params['Intercept'], ci_low=ci[0], ci_high=ci[1],
                          p_two_sided=r.pvalues['Intercept'], sd_state=sd['state'], sd_family_year=sd['fy'], converged=bool(r.converged)))
    pd.DataFrame(forest).to_csv(OUT/'forest_by_state.csv', index=False)
    pd.DataFrame(mixed).to_csv(OUT/'mixed_model.csv', index=False)
    (OUT/'README.md').write_text('# Registered-test scorecard (descriptive additions)\n\nscorecard.csv: every registered typed-vs-pooled hypothesis with its registered decision and a 95% t interval over its units (descriptive, unadjusted; the registered tests are the sign-flip tests). forest_by_state.csv: per-state lead-1 typed minus pooled MASE with 95% t intervals over family-years, 14 new states. mixed_model.csv: linear mixed model diff ~ 1 with crossed random effects for state and family-year (REML), both tests pooled; converged flag reported. Written after both registered analyses; exploratory.\n')
    print(sc.round(4).to_string(index=False)); print(pd.DataFrame(mixed).round(4).to_string(index=False))


if __name__ == '__main__':
    main()
