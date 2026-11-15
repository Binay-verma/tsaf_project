"""Early-period (2015-2020) festival-effect heterogeneity for the seven second-test states, BEFORE registration.

Uses only 2015-2020 demand and the second-test calendar (no forecast, no 2021-2025 data). The design (M1, M2)
already fixes h to come from these years; it is computed now to check that M1 and M2 can work. Two measures:
  h      = between-family SD of log effects, net of sampling noise, divided by |mean effect| (the registered first-test h)
  h_abs  = the same SD without the division (absolute dispersion)
Run: python src/new_states_v2_early_h_v1.py
"""
from pathlib import Path
import sys
import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
import simulation_calibration_v1 as c1  # noqa: E402

S = ['Punjab', 'Haryana', 'West Bengal', 'Kerala', 'Bihar', 'Odisha', 'Chhattisgarh']


def frame(y, a, st):
    idx = y.index
    X = pd.get_dummies(idx.year.astype(str), prefix='y').set_index(idx).astype(float)
    X = X.join(pd.get_dummies(idx.dayofweek, prefix='dow', drop_first=True).set_index(idx).astype(float))
    doy = idx.dayofyear.values
    for j in (1, 2, 3):
        X[f's{j}'] = np.sin(2*np.pi*j*doy/365.25); X[f'c{j}'] = np.cos(2*np.pi*j*doy/365.25)
    fams = sorted(a[a.state == st].family.unique())
    for f in fams:
        X[f] = idx.isin(pd.to_datetime(a[(a.state == st) & (a.family == f)].date)).astype(float)
    return X, fams


def main():
    o = pd.read_csv(ROOT/'data/external/new_states_v2_energy_GWh.csv', index_col=0, parse_dates=True)
    a = pd.read_csv(ROOT/'review/new_states_v2/calendar_entries_2015_2025.csv'); a = a[a.year <= 2020]
    rows = []
    for st in S:
        y = o[st].where(o[st] > 0); y = y[(y.index.year >= 2015) & (y.index.year <= 2020)]
        X, fams = frame(y, a, st)
        ly = np.log(y); ok = ly.notna()
        beta, *_ = np.linalg.lstsq(X[ok].to_numpy(), ly[ok].to_numpy(), rcond=None)
        r = ly[ok].to_numpy()-X[ok].to_numpy()@beta
        cov = np.linalg.pinv(X[ok].to_numpy().T@X[ok].to_numpy())*(r@r/(ok.sum()-X.shape[1]))
        cols = list(X.columns); b = np.array([beta[cols.index(f)] for f in fams]); se2 = np.array([cov[cols.index(f), cols.index(f)] for f in fams])
        e = c1.estimate(ly, X, fams)
        rows.append(dict(state=st, families=len(fams), mean_log_effect=b.mean(), h=e['h'], h_abs=np.sqrt(max(0., b.var(ddof=1)-se2.mean())),
                         **{f'effect_{f}': np.exp(v)-1 for f, v in zip(fams, b)}))
    d = pd.DataFrame(rows)
    out = ROOT/'review/new_states_v2/power'; out.mkdir(parents=True, exist_ok=True)
    d.to_csv(out/'early_heterogeneity_2015_2020.csv', index=False)
    print(d.round(3).to_string(index=False))


if __name__ == '__main__':
    main()
