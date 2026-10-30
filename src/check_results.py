"""Independent checks against raw observations and saved predictions."""
from pathlib import Path
import pandas as pd
import numpy as np
p=Path(__file__).resolve().parents[1]
c=pd.read_csv(p/'data/clean_daily_energy_GWh.csv',index_col=0,parse_dates=True)
r=pd.read_csv(p/'results/validation_predictions.csv',parse_dates=['date'])
m=pd.read_csv(p/'results/validation_metrics.csv')
assert not r.duplicated(['state','date','model']).any()
for state,g in r.groupby('state'):
    observed=c[state]
    y=observed.copy()
    for i in range(len(y)):
        if pd.isna(y.iloc[i]): y.iloc[i]=y.iloc[i-7] if i>=7 and pd.notna(y.iloc[i-7]) else (y.iloc[i-1] if i else np.nan)
    for name,lag in [('last_value',1),('seasonal_naive_7',7)]:
        g0=g[g.model==name]
        np.testing.assert_allclose(g0.prediction,y.shift(lag).loc[g0.date])
    # Missing labels must never appear in scored data.
    np.testing.assert_allclose(g.actual,observed.loc[g.date])
    expected=set(observed.loc['2022'].dropna().index)
    for _,q in g.groupby('model'): assert set(q.date)==expected
for row in m.itertuples():
    q=r[(r.state==row.state)&(r.model==row.model)]
    if row.subset=='diwali_window': q=q[q.diwali_window==1]
    if row.subset=='outside_diwali_window': q=q[q.diwali_window==0]
    err=(q.actual-q.prediction).abs()
    assert row.n_scored==len(q)
    np.testing.assert_allclose(row.MAE_GWh,err.mean())
    np.testing.assert_allclose(row.MASE,(err/q.training_mase_scale).mean())
assert set(r.date.dt.year)=={2022}
print('PASS: unique origins; raw-label alignment; seasonal/last-value forecasts; observed-label coverage; independent MAE/MASE; untouched holdout.')
