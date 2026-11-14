"""Out-of-time check of the per-state prediction (EXPLORATORY, after the registered analysis).

simulation_calibration_v2 measured h on 2017-2025, the same years whose forecasts it was compared with, so its
agreement could be partly circular. Here, for the seven new states:
  * calibrate (mu, h, phi, sigma, omega) on 2015-2020 only;
  * simulate the ridge crossover h* at those early parameters (30 replications per grid point);
  * predict typed or pooled for each state;
  * compare with observed typed-minus-pooled lead-1 MASE on 2021-2025 forecasts only.

Run: python src/simulation_calibration_v3_timesplit.py
"""
from multiprocessing import Pool
from pathlib import Path
import sys
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
import simulation_calibration_v1 as c1   # noqa: E402
import simulation_calibration_v2 as c2   # noqa: E402
import simulation_typed_pooled_v2 as s2  # noqa: E402

OUT = ROOT/'results/simulation_calibration_v3_timesplit'
EARLY, LATE = range(2015, 2021), range(2021, 2026)


def frame(state, a, years):
    y = c2.series(state)
    y = y[y.index.year.isin(list(years))]
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


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    a = pd.read_csv(ROOT/'results/new_states_v1/anchors_2015_2025.csv')
    a = a[a.year.isin(list(EARLY))][['state', 'family', 'year', 'date']].drop_duplicates()
    est = []
    for st in c2.NEW:
        e = c1.estimate(*frame(st, a, EARLY))
        est.append(dict(state=st, **{k: float(e[k]) for k in ['mu', 'h', 'phi', 'sigma', 'omega', 'families']}))
    est = pd.DataFrame(est)
    tasks = [(r.state, r.mu, r.phi, r.sigma, r.omega, h, k) for r in est.itertuples() for h in c2.H_GRID for k in range(c2.REPS)]
    with Pool(2) as pool:
        sim = pd.DataFrame(pool.map(c2.sim_task, tasks))
    sim.to_csv(OUT/'per_state_simulation_early.csv', index=False)
    curve = sim.groupby(['state', 'h'])['diff'].mean().rename('mean').reset_index()
    est['h_crossover'] = est.state.map(curve.groupby('state').apply(s2.crossover, include_groups=False))
    est['predicted_linear'] = np.where(est.h > est.h_crossover, 'typed', 'pooled')
    est.to_csv(OUT/'calibration_2015_2020.csv', index=False)
    obs = c2.observed_years(LATE).merge(est[['state', 'h', 'h_crossover', 'predicted_linear']], on='state')
    obs['observed'] = np.where(obs.observed_typed_minus_pooled < 0, 'typed', 'pooled')
    obs['agree'] = obs.observed == obs.predicted_linear
    obs.to_csv(OUT/'predicted_2015_2020_vs_observed_2021_2025.csv', index=False)
    agree = obs.groupby('model').agree.agg(['sum', 'count']).reset_index()
    agree.to_csv(OUT/'agreement_by_model.csv', index=False)
    print(est.round(3).to_string(index=False)); print(obs.round(4).to_string(index=False)); print(agree.to_string(index=False))


if __name__ == '__main__':
    main()
