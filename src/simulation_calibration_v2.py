"""Ten-state calibration and per-state crossover (EXPLORATORY; written after the registered new-states analysis).

1. Calibrate (mu, h, phi, sigma, omega) separately for each of the ten states: the three original states
   (Delhi, Karnataka, Maharashtra) and the seven new states. Same model and estimators as
   simulation_calibration_v1, on 2017-2025 complete days with each state's own in-scope families.
   Uncertainty: 300 year-bootstrap draws per state.
2. For each state, simulate ridge typed-vs-pooled at that state's own (mu, phi, sigma, omega) over an h grid
   (30 replications per point) and find the crossover h* where typed starts to win.
   Prediction: typed better for linear models if h_state > h*_state.
3. Compare with the observed typed-minus-pooled lead-1 MASE per state in the new-states forecasts (ridge,
   SARIMAX, leaf-2 LightGBM, LightGBM, Chronos-2, TimesFM-3).

All of this comes after the registered decisions, so none of it is confirmatory. Nothing registered is changed.

Run: python src/simulation_calibration_v2.py
"""
import json
import sys
from multiprocessing import Pool
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
import simulation_calibration_v1 as c1   # noqa: E402
import simulation_typed_pooled_v2 as s2  # noqa: E402

OUT = ROOT/'results/simulation_calibration_v2'
ORIGINAL = ['Delhi', 'Karnataka', 'Maharashtra']
NEW = ['Uttar Pradesh', 'Rajasthan', 'Madhya Pradesh', 'Gujarat', 'Telangana', 'Andhra Pradesh', 'Tamil Nadu']
H_GRID = [0., 0.1, 0.2, 0.3, 0.45, 0.6, 0.8, 1.0, 1.5]
BOOT, REPS, SEED = 300, 30, 20261115


def anchors():
    a = c1.anchors()
    b = pd.read_csv(ROOT/'results/new_states_v1/anchors_2015_2025.csv')
    b = b[b.year.isin(c1.YEARS)]   # all anchor roles, as in v1 and in the forecasting frames
    return pd.concat([a, b[['state', 'family', 'year', 'date']]]).drop_duplicates()


def series(state):
    f = 'latest_state_energy_GWh.csv' if state in ORIGINAL else 'new_states_energy_GWh.csv'
    y = pd.read_csv(ROOT/'data/external'/f, parse_dates=['date']).set_index('date')[state]
    return y.where(y > 0)


def frame(state, a):
    """Same design matrix as simulation_calibration_v1.frame, for any of the ten states."""
    y = series(state)
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


def boot(ly, X, fams, rng):
    yrs = np.array(list(c1.YEARS))
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
    return c1.estimate(lyb, Xb, fams)


def sim_task(t):
    state, mu, phi, sigma, omega, h, rep = t
    rng = np.random.default_rng([SEED, abs(hash(state)) % 10**6, int(round(h*1000)), rep])
    y, flags = s2.generate(rng, mu, h, phi, sigma, omega)
    X = s2.local_X(y, flags)
    d = []
    for year in s2.EVENT_YEARS:
        start = s2.DAYS.get_loc(pd.Timestamp(year, 1, 1))
        sc = s2.scale(y, start)
        tr = np.arange(7, start)
        te = np.where((s2.DAYS.year == year) & (flags.sum(axis=1) > 0))[0]
        e = {arm: np.abs(s2.fit_predict('ridge', 0, M[tr], y[tr], M[te]) - y[te])/sc for arm, M in X.items()}
        d.append(float(np.mean(e['typed'] - e['pooled'])))
    return dict(state=state, h=h, rep=rep, diff=float(np.mean(d)))


def observed():
    rows = []
    base = ROOT/'results/new_states_v1'
    for cohort, models in [('event_window', ['ridge', 'lightgbm', 'lightgbm_capacity2', 'sarimax']),
                           ('fm_2017_2020', ['chronos', 'timesfm']), ('fm_2021_2025', ['chronos', 'timesfm'])]:
        for m in models:
            p = pd.read_csv(base/cohort/m/'predictions.csv')
            p = p[(p.horizon == 1) & p.arm.isin(['day5', 'pooled_day5'])]
            p['MASE'] = (p.prediction - p.actual).abs()/p.mase_scale
            rows.append(p[['model', 'state', 'family', 'year', 'arm', 'MASE']])
    d = pd.concat(rows)
    s = d.groupby(['model', 'state', 'family', 'year', 'arm']).MASE.mean().unstack('arm')
    s = (s['day5'] - s['pooled_day5']).rename('diff').reset_index()
    g = s.groupby(['model', 'state'])['diff']
    return pd.DataFrame({'observed_typed_minus_pooled': g.mean(), 'se': g.std()/np.sqrt(g.count()), 'family_years': g.count()}).reset_index()


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    a = anchors()
    rng = np.random.default_rng(SEED)
    est, bt = [], []
    for st in ORIGINAL + NEW:
        ly, X, fams = frame(st, a)
        e = c1.estimate(ly, X, fams)
        est.append(dict(state=st, panel='original' if st in ORIGINAL else 'new', **{k: e[k] for k in ['mu', 'h', 'phi', 'sigma', 'omega', 'families']}))
        for b in range(BOOT):
            r = boot(ly, X, fams, rng)
            bt.append(dict(state=st, boot=b, h=r['h'], mu=r['mu']))
        print('calibrated', st, flush=True)
    est = pd.DataFrame(est)
    bt = pd.DataFrame(bt)
    q = bt.groupby('state').h.quantile([.05, .95]).unstack()
    est['h_lo'] = est.state.map(q[.05]); est['h_hi'] = est.state.map(q[.95])
    tasks = [(r.state, r.mu, r.phi, r.sigma, r.omega, h, k) for r in est.itertuples() for h in H_GRID for k in range(REPS)]
    with Pool(2) as pool:
        sim = pd.DataFrame(pool.map(sim_task, tasks))
    sim.to_csv(OUT/'per_state_simulation.csv', index=False)
    curve = sim.groupby(['state', 'h'])['diff'].mean().rename('mean').reset_index()
    est['h_crossover'] = est.state.map(curve.groupby('state').apply(s2.crossover, include_groups=False))
    est['predicted_linear'] = np.where(est.h > est.h_crossover, 'typed', 'pooled')
    est.to_csv(OUT/'calibration_by_state.csv', index=False)
    bt.to_csv(OUT/'bootstrap_by_state.csv', index=False)
    obs = observed()
    obs = obs.merge(est[['state', 'h', 'h_lo', 'h_hi', 'h_crossover', 'predicted_linear']], on='state')
    obs.to_csv(OUT/'predicted_vs_observed_new_states.csv', index=False)
    figure(est, curve, obs)
    print(est.round(3).to_string(index=False))
    print(obs.round(4).to_string(index=False))


def figure(est, curve, obs):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    ax = axes[0]
    e = est.sort_values('h').reset_index(drop=True)
    for i, r in e.iterrows():
        col = 'C0' if r.panel == 'original' else 'C1'
        ax.plot([r.h_lo, r.h_hi], [i, i], color=col, lw=1.2)
        ax.plot(r.h, i, 'o', color=col)
        ax.plot(r.h_crossover, i, 'k|', ms=10)
    ax.set_yticks(range(len(e))); ax.set_yticklabels(e.state, fontsize=8)
    ax.set_xlabel('festival-effect heterogeneity h (dot, 90% band)\n| = simulated crossover for that state')
    ax.set_title('Where each state sits')
    ax.plot([], [], 'o', color='C0', label='original 3'); ax.plot([], [], 'o', color='C1', label='new 7'); ax.legend(fontsize=7)
    ax = axes[1]
    for m, mk in zip(['ridge', 'sarimax', 'lightgbm_capacity2', 'timesfm'], 'osd^'):
        x = obs[obs.model == m].copy()
        x['margin'] = x.h - x.h_crossover
        ax.errorbar(x.margin, x.observed_typed_minus_pooled, yerr=1.96*x.se, fmt=mk, capsize=2, label=m, alpha=.8)
    ax.axhline(0, color='grey', lw=.8); ax.axvline(0, color='grey', lw=.8)
    ax.set_xlabel('h minus crossover (> 0: simulation predicts typed for linear models)')
    ax.set_ylabel('observed typed minus pooled\nlead-1 MASE (< 0: typed better)')
    ax.set_title('Exploratory: new states, after the registered test'); ax.legend(fontsize=7)
    fig.tight_layout(); fig.savefig(OUT/'states_on_curve.png', dpi=200)


if __name__ == '__main__':
    main()
