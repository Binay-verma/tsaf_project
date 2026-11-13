"""Calibrate the typed-vs-pooled simulation to the ORIGINAL three-state panel (Delhi, Karnataka, Maharashtra).

Uses only data already analysed in v9 (no new-states data, no forecasts). Descriptive only: nothing
here is tuned to any forecast result.

Model per state, on log demand 2016-2025 (complete days only):
    log y = year dummies + day-of-week + annual Fourier(3) + one flag per festival family + r_t
Then:
    mu    = mean of the five family effects (exp(beta) - 1)
    h     = sqrt(max(0, var(beta) - mean(se^2))) / |mu|     (spread net of estimation noise; z has sd 1)
    phi   = AR(1) coefficient of r on non-event days
    sigma = sd of the AR(1) innovations x 100 (generator level is 100)
    omega = sqrt(max(0, var(r | event day) - var(r | other day))) / |mu|
Uncertainty: 1,000 bootstrap draws resampling calendar years within each state.

Run: python src/simulation_calibration_v1.py   (writes results/simulation_calibration_v1/)
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'results/simulation_calibration_v1'
FAMILIES = ['Diwali', 'Dussehra', 'Holi', 'Ganesh_Chaturthi', 'Ugadi_Gudi_Padwa']
YEARS = range(2017, 2026)
BOOT, SEED = 1000, 20261114


def anchors():
    a = pd.concat([pd.read_csv(ROOT/'results/longer_panel_stage_b_v1/anchors_2017_2021.csv'),
                   pd.read_csv(ROOT/'results/longer_panel_stage_a_v1/anchors_2020_2025.csv')])
    a = a[a.year.isin(YEARS)][['state', 'family', 'year', 'date']].drop_duplicates()
    return a


def frame(state, a):
    y = pd.read_csv(ROOT/'data/external/latest_state_energy_GWh.csv', parse_dates=['date']).set_index('date')[state]
    y = y[(y.index.year >= 2017) & (y.index.year <= 2025)]
    idx = y.index
    X = pd.get_dummies(idx.year.astype(str), prefix='y').set_index(idx).astype(float)
    X = X.join(pd.get_dummies(idx.dayofweek, prefix='dow', drop_first=True).set_index(idx).astype(float))
    doy = idx.dayofyear.values
    for j in (1, 2, 3):
        X[f's{j}'] = np.sin(2*np.pi*j*doy/365.25); X[f'c{j}'] = np.cos(2*np.pi*j*doy/365.25)
    fams = sorted(a[a.state == state].family.unique())
    for f in fams:
        X[f] = idx.isin(pd.to_datetime(a[(a.state == state) & (a.family == f)].date)).astype(float)
    return np.log(y), X, fams


def estimate(ly, X, fams):
    ok = ly.notna()
    Xo, yo = X[ok].to_numpy(), ly[ok].to_numpy()
    beta, *_ = np.linalg.lstsq(Xo, yo, rcond=None)
    r = pd.Series(np.nan, index=ly.index); r[ok] = yo - Xo@beta
    dof = len(yo) - Xo.shape[1]
    cov = np.linalg.pinv(Xo.T@Xo)*(np.nansum(r**2)/dof)
    cols = list(X.columns)
    b = np.array([beta[cols.index(f)] for f in fams]); se = np.sqrt([cov[cols.index(f), cols.index(f)] for f in fams])
    effects = np.exp(b) - 1
    mu = effects.mean()
    h = np.sqrt(max(0., b.var(ddof=1) - np.mean(se**2)))/abs(np.mean(b))
    event = X[fams].sum(axis=1) > 0
    rn = r.where(~event)
    phi = (rn*rn.shift(1)).sum()/(rn.shift(1)**2)[rn.notna()].sum()
    sigma = 100*np.nanstd(rn - phi*rn.shift(1))
    omega = np.sqrt(max(0., np.nanvar(r[event]) - np.nanvar(rn)))/abs(mu)
    return dict(mu=mu, h=h, phi=phi, sigma=sigma, omega=omega, families=len(fams),
                **{f'effect_{f}': e for f, e in zip(fams, effects)})


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    a = anchors()
    rng = np.random.default_rng(SEED)
    rows, boots = [], []
    for state in ['Delhi', 'Karnataka', 'Maharashtra']:
        ly, X, fams = frame(state, a)
        rows.append(dict(state=state, **estimate(ly, X, fams)))
        yrs = np.array(list(YEARS))
        for b in range(BOOT):
            pick = rng.choice(yrs, len(yrs))
            parts = []
            for k, yr in enumerate(pick):
                m = ly.index.year == yr
                Xi = X[m].copy()
                Xi[[c for c in X.columns if c.startswith('y_')]] = 0.
                Xi[f'y_b{k}'] = 1.
                parts.append((ly[m].reset_index(drop=True), Xi.reset_index(drop=True)))
            lyb = pd.concat([p[0] for p in parts], ignore_index=True)
            Xb = pd.concat([p[1] for p in parts], ignore_index=True).fillna(0.)
            Xb = Xb.drop(columns=[c for c in Xb.columns if c.startswith('y_') and not c.startswith('y_b')])
            e = estimate(lyb, Xb, fams)
            boots.append(dict(state=state, boot=b, **{k: e[k] for k in ['mu', 'h', 'phi', 'sigma', 'omega']}))
    est = pd.DataFrame(rows); bt = pd.DataFrame(boots)
    est.to_csv(OUT/'estimates_by_state.csv', index=False)
    bt.to_csv(OUT/'bootstrap.csv', index=False)
    pooled = bt.groupby('boot')[['mu', 'h', 'phi', 'sigma', 'omega']].mean()
    point = est[['mu', 'h', 'phi', 'sigma', 'omega']].mean()
    summ = {k: dict(point=float(point[k]), lo=float(pooled[k].quantile(.05)), hi=float(pooled[k].quantile(.95))) for k in point.index}
    (OUT/'calibration.json').write_text(json.dumps(dict(note='Three-state mean; 90% band from year bootstrap (lag effects of shuffled year boundaries ignored)',
                                                        **summ), indent=1))
    print(est.round(4).to_string(index=False)); print(json.dumps(summ, indent=1))


if __name__ == '__main__':
    main()
