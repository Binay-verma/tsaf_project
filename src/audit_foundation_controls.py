"""Read-only audit and prespecified contrast tables for model controls."""
from pathlib import Path
import argparse
import hashlib
import json
import numpy as np
import pandas as pd
from forecasting import ROOT, load_data
from calendar_controls import covariates, placebo_shifts

OUT = ROOT/'results/mechanism_controls_v1'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', required=True, choices=['chronos2','timesfm3'])
    args = parser.parse_args()
    out = OUT/args.model
    d = pd.read_csv(out/'predictions.csv', parse_dates=['origin','date'])
    protocol = json.loads((OUT/'protocol.json').read_text())
    source = load_data('latest')
    cases = pd.read_csv(OUT/'cases.csv', parse_dates=['origin','date'])
    assert hashlib.sha256((OUT/'cases.csv').read_bytes()).hexdigest() == protocol['cases_sha256']
    expected = set(map(tuple, cases[['state','origin','horizon']].to_numpy()))
    assert len(d) == 1350 and set(d.arm) == set(protocol['arms'])
    assert not d.duplicated(['state','origin','horizon','arm']).any()
    assert np.isfinite(d.prediction).all() and ((d.date-d.origin).dt.days == d.horizon-1).all()
    for (state,year), g in d.groupby(['state','year']):
        np.testing.assert_allclose(g.actual, source[state].reindex(g.date))
        cutoff = pd.Timestamp(f'{year-1}-12-31')
        tr = source[state].loc[cutoff-pd.Timedelta(days=729):cutoff]
        np.testing.assert_allclose(g.mase_scale, (tr-tr.shift(7)).abs().mean())
    for _, g in d.groupby('arm'):
        assert set(map(tuple, g[['state','origin','horizon']].to_numpy())) == expected
    d['ae'] = abs(d.actual-d.prediction)
    d['scaled'] = d.ae/d.mase_scale
    m = d.groupby(['state','year','horizon','arm']).agg(MAE_GWh=('ae','mean'),MASE=('scaled','mean'),n=('ae','size')).reset_index()
    m.to_csv(out/'metrics_state_year.csv',index=False)
    macro = m.groupby(['year','horizon','arm']).MASE.mean().reset_index()
    macro.to_csv(out/'metrics_year.csv',index=False)
    macro.groupby(['horizon','arm']).MASE.mean().reset_index().to_csv(out/'metrics_two_year.csv',index=False)
    per_case = d.pivot(index=['state','origin','horizon'],columns='arm',values='prediction')
    zeros = {arm:dict(max_prediction_change=float(abs(per_case[arm]-per_case.calendar).max()),
                      mean_prediction_change=float(abs(per_case[arm]-per_case.calendar).mean()))
             for arm in ['zero_1','zero_7']}
    piv = m.pivot(index=['state','year','horizon'],columns='arm',values='MAE_GWh')
    contrasts=[]
    pairs=[('regional_window','generic_window'),('regional_7','generic_7'),
           ('zero_1','calendar'),('zero_7','calendar'),('regional_7','placebo_7')]
    for arm,reference in pairs:
        effect=(100*(piv[reference]-piv[arm])/piv[reference]).rename('improvement_pct').reset_index()
        for (year,horizon), g in effect.groupby(['year','horizon']):
            contrasts.append(dict(arm=arm,reference=reference,year=int(year),horizon=int(horizon),
                                  mean_state_improvement_pct=float(g.improvement_pct.mean())))
    pd.DataFrame(contrasts).to_csv(out/'contrasts_year.csv',index=False)
    pd.DataFrame(contrasts).groupby(['arm','reference','horizon']).mean_state_improvement_pct.mean().reset_index().to_csv(
        out/'contrasts_two_year.csv',index=False)
    # Names may differ but generic/regional data are identical for Delhi (no regional extras).
    p=per_case.loc['Delhi']
    delhi_differences={}
    for a,b in [('generic_window','regional_window'),('generic_7','regional_7')]:
        delta=float(abs(p[a]-p[b]).max());delhi_differences[a+'/'+b]=delta
        np.testing.assert_allclose(p[a],p[b],rtol=2e-4,atol=1e-3)
    protected=json.loads((ROOT/'results/strong_refit_v1/protected_before.json').read_text())
    assert all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h for n,h in protected.items())
    frozen=ROOT/'results/prospective_20261030_v1'
    assert hashlib.sha256((frozen/'predictions.csv').read_bytes()).hexdigest()==json.loads((frozen/'freeze.json').read_text())['predictions_sha256']
    report=dict(status='passed',model=args.model,rows=len(d),cases_per_arm=len(expected),
        zero_channel_sensitivity=zeros,delhi_identical_information_checks=delhi_differences,
        quantile_crossings=int((np.diff(d[[c for c in d if c.startswith('q_')]].to_numpy(),axis=1)<0).sum()),
        protected_historical_files=len(protected),frozen_forecasts_unchanged=True,
        caveat='Two historical event clusters; one seeded placebo; dimension controls do not establish a causal provenance mechanism')
    (out/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
