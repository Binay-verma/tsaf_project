"""Per-state, out-of-time predictions from the pipeline-matched simulation (EXPLORATORY; after the registered analysis;
design committed before running).

For each of the seven further states, the generator of simulation_typed_pooled_v3 (window profile, 730-day monthly refits,
all window days scored) is run with that state's own parameters (mu, h, phi, sigma, omega) estimated on 2015-2020 only
(results/simulation_calibration_v3_timesplit/calibration_2015_2020.csv). Outputs per state:
  * Ridge crossover h* over an h grid (30 replications per point) and the predicted direction (typed if h > h*);
  * predicted typed - pooled MASE at the state's own h for Ridge, LightGBM leaf 2 and leaf 5 (30 replications);
then compared with the observed 2021-2025 typed - pooled lead-1 MASE (new-states registered forecasts).
This replaces the v2-based thresholds of results/simulation_calibration_v2/v3_timesplit, whose generator did not match
the pipeline. Uttar Pradesh (mu about 0 or positive) has no defined crossover.
Run: python src/simulation_states_v3.py
"""
import json
import sys
import zlib
from multiprocessing import Pool
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
import simulation_typed_pooled_v2 as s2   # noqa: E402
import simulation_typed_pooled_v3 as s3   # noqa: E402
import simulation_calibration_v2 as c2    # noqa: E402

OUT = ROOT/'results/simulation_states_v3'
H_GRID = [0., 0.15, 0.3, 0.45, 0.6, 0.8, 1.0, 1.5]
REPS, SEED = 30, 20261116
STABLE = '--stable-seed' in sys.argv
if STABLE:
    OUT = ROOT/'results/simulation_states_v3_seedcheck'   # rerun with a process-independent seed
MODELS = {'ridge': 0, 'lgbm_leaf2': 2, 'lgbm_leaf5': 5}


def task(t):
    state, params, model, h, rep = t
    s3.P0 = dict(params)                      # generator reads mu, phi, sigma, omega from P0
    key = zlib.crc32(state.encode()) % 10**6 if STABLE else abs(hash(state)) % 10**6   # hash() is randomised per process
    rng = np.random.default_rng([SEED, key, int(round(h*1000)), rep, MODELS[model]])
    out = run_one(model, h, rng)
    return dict(state=state, model=model, h=h, rep=rep, typed_minus_pooled=out)


def run_one(model, h, rng):
    leaf = MODELS[model]
    y, flags, window = s3.generate(rng, h)
    X = s2.local_X(y, flags)
    diffs = []
    for year in s3.EVENT_YEARS:
        start = s3.DAYS.get_loc(pd.Timestamp(year, 1, 1))
        sc = s2.scale(y, start)
        te_all = np.where((s3.DAYS.year == year) & window)[0]
        err = {a: [] for a in X}
        for month in sorted(set(s3.DAYS[te_all].month)):
            te = te_all[s3.DAYS[te_all].month == month]
            m0 = s3.DAYS.get_loc(pd.Timestamp(year, month, 1))
            tr = np.arange(max(7, m0 - 730), m0)
            for arm, M in X.items():
                p = s2.fit_predict('ridge' if model == 'ridge' else 'lgbm', leaf, M[tr], y[tr], M[te])
                err[arm].append(np.abs(p - y[te])/sc)
        diffs.append(float(np.mean(np.concatenate(err['typed'])) - np.mean(np.concatenate(err['pooled']))))
    return float(np.mean(diffs))


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    cal = pd.read_csv(ROOT/'results/simulation_calibration_v3_timesplit/calibration_2015_2020.csv')
    tasks = []
    for r in cal.itertuples():
        params = dict(mu=r.mu, h=r.h, phi=r.phi, sigma=r.sigma, omega=r.omega)
        if r.mu < 0:
            tasks += [(r.state, params, 'ridge', h, k) for h in H_GRID for k in range(REPS)]
        tasks += [(r.state, params, m, round(float(r.h), 3), k) for m in MODELS for k in range(REPS)]
    (OUT/'design.json').write_text(json.dumps(dict(h_grid=H_GRID, reps=REPS, seed=SEED, models=MODELS, calibration='2015-2020 per state'), indent=1))
    with Pool(2) as pool:
        res = pool.map(task, tasks)
    d = pd.DataFrame(res)
    d.to_csv(OUT/'raw.csv', index=False)
    summary(cal, d)


def summary(cal, d):
    rows = []
    for r in cal.itertuples():
        x = d[(d.state == r.state) & (d.model == 'ridge')]
        curve = x[x.h.isin(H_GRID)].groupby('h').typed_minus_pooled.mean().rename('mean').reset_index()
        hstar = s2.crossover(curve) if len(curve) and r.mu < 0 else np.nan
        row = dict(state=r.state, mu=r.mu, h=r.h, h_crossover=hstar,
                   predicted_ridge_direction=('typed' if (np.isfinite(hstar) and r.h > hstar) else 'pooled'))
        for m in MODELS:
            y = d[(d.state == r.state) & (d.model == m) & (d.h == round(float(r.h), 3))].typed_minus_pooled
            row[f'predicted_{m}'] = float(y.mean())
        rows.append(row)
    P = pd.DataFrame(rows)
    obs = c2.observed_years(range(2021, 2026))
    obs = obs.pivot(index='state', columns='model', values='observed_typed_minus_pooled').add_prefix('observed_').reset_index()
    P = P.merge(obs, on='state')
    P.to_csv(OUT/'predicted_vs_observed_2021_2025.csv', index=False)
    agree = {m: int(((P[f'predicted_ridge_direction'] == 'typed') == (P[f'observed_{m}'] < 0)).sum()) for m in ['ridge', 'sarimax', 'lightgbm_capacity2', 'timesfm']}
    means = dict(predicted_ridge=float(P.predicted_ridge.mean()), observed_ridge=float(P.observed_ridge.mean()),
                 predicted_leaf2=float(P.predicted_lgbm_leaf2.mean()), observed_leaf2=float(P.observed_lightgbm_capacity2.mean()),
                 predicted_leaf5=float(P.predicted_lgbm_leaf5.mean()), observed_stable_lgbm=float(P.observed_lightgbm.mean()),
                 predicted_stable_mix_0556=float(0.556*P.predicted_lgbm_leaf5.mean()))
    (OUT/'summary.json').write_text(json.dumps(dict(direction_agreement_of_7=agree, state_means=means), indent=1))
    print(P.round(4).to_string(index=False)); print(json.dumps(dict(agree=agree, means=means), indent=1))


if __name__ == '__main__':
    main()
