"""Simulation v3: closer to the empirical pipeline (EXPLORATORY; written after the registered analysis, design committed
before running). Purpose: v2 reproduced directions but its effect sizes were about ten times the observed ones. v3 changes
three things to match the empirical protocol, and nothing else:
  1. festival effects spread over the window with the profile measured on the three original states (offsets -3..+3,
     relative to the festival day): PROFILE below;
  2. local models are refitted monthly on the 730 days before the refit month (as in the empirical engine), instead of
     on all earlier years;
  3. every target day in the +-3-day festival window is scored (one step ahead, observed lags), not only the festival day.
Flags are still on the festival day only (the empirical day5 / pooled_day5 arms).
Calibration: the three-state values of results/simulation_calibration_v1 (unchanged).
Compared afterwards with observed typed - pooled lead-1 MASE: Stage A (three original states) and the new states.
Run: python src/simulation_typed_pooled_v3.py run ; python src/simulation_typed_pooled_v3.py summarise
"""
import json
import sys
from multiprocessing import Pool
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
import simulation_typed_pooled_v2 as s2  # noqa: E402

OUT = ROOT/'results/simulation_typed_pooled_v3'
PROFILE = [-0.087, -0.140, 0.069, 1.0, 0.637, 0.299, 0.133]   # offsets -3..+3, measured on Delhi/Karnataka/Maharashtra
P0 = s2.P0
H_GRID = [0., 0.25, round(P0['h'], 3), 1., 2.]
MODELS = {'ridge': (0, 100), 'lgbm_leaf20': (20, 30), 'lgbm_leaf5': (5, 30), 'lgbm_leaf2': (2, 30)}
SEED = 20261115
DAYS, EVENT_YEARS, BASE_DOY, Z = s2.DAYS, s2.EVENT_YEARS, s2.BASE_DOY, s2.Z


def generate(rng, h):
    n = len(DAYS)
    doy = DAYS.dayofyear.values
    weekly = np.array([0., -0.01, -0.01, -0.01, -0.01, -0.02, -0.06])[DAYS.dayofweek.values]
    annual = 0.08*np.sin(2*np.pi*doy/365.25) + 0.03*np.cos(4*np.pi*doy/365.25)
    innov = rng.normal(0, P0['sigma'], n)
    noise = np.zeros(n)
    for i in range(1, n):
        noise[i] = P0['phi']*noise[i-1] + innov[i]
    base = 100*(1 + 0.00002*np.arange(n))*(1 + weekly + annual)
    flags, mult, window = np.zeros((n, 5)), np.ones(n), np.zeros(n, bool)
    for y in range(2015, 2026):
        for k, d0 in enumerate(BASE_DOY):
            i = DAYS.get_loc(pd.Timestamp(y, 1, 1) + pd.Timedelta(days=int(d0 + rng.integers(-15, 16)) - 1))
            flags[i, k] = 1.
            e = P0['mu']*(1 + h*Z[k]) + P0['omega']*abs(P0['mu'])*rng.normal()
            for off, w in zip(range(-3, 4), PROFILE):
                mult[i+off] *= 1 + e*w
                window[i+off] = True
    return base*mult + noise, flags, window


def one(task):
    model, h, rep = task
    leaf, _ = MODELS[model]
    rng = np.random.default_rng([SEED, int(round(h*1000)), rep])
    y, flags, window = generate(rng, h)
    X = s2.local_X(y, flags)
    diffs = []
    for year in EVENT_YEARS:
        start = DAYS.get_loc(pd.Timestamp(year, 1, 1))
        sc = s2.scale(y, start)
        te_all = np.where((DAYS.year == year) & window)[0]
        err = {a: [] for a in X}
        for month in sorted(set(DAYS[te_all].month)):
            te = te_all[DAYS[te_all].month == month]
            m0 = DAYS.get_loc(pd.Timestamp(year, month, 1))
            tr = np.arange(max(7, m0 - 730), m0)
            for arm, M in X.items():
                p = s2.fit_predict('ridge' if model == 'ridge' else 'lgbm', leaf, M[tr], y[tr], M[te])
                err[arm].append(np.abs(p - y[te])/sc)
        diffs.append(float(np.mean(np.concatenate(err['typed'])) - np.mean(np.concatenate(err['pooled']))))
    return dict(model=model, h=h, rep=rep, typed_minus_pooled=float(np.mean(diffs)))


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/'design.json').write_text(json.dumps(dict(profile=PROFILE, calibration=P0, h_grid=H_GRID, models={k: list(v) for k, v in MODELS.items()},
                                                   seed=SEED, training='730 days before each refit month', scoring='all days in +-3 windows'), indent=1))
    tasks = [(m, h, r) for m, (_, reps) in MODELS.items() for h in H_GRID for r in range(reps)]
    with Pool(2) as pool:
        res = pool.map(one, tasks)
    pd.DataFrame(res).to_csv(OUT/'raw.csv', index=False)


def summarise():
    d = pd.read_csv(OUT/'raw.csv')
    s = d.groupby(['model', 'h']).typed_minus_pooled.agg(['mean', 'std', 'count']).reset_index()
    s['mc_se'] = s['std']/np.sqrt(s['count'])
    s.drop(columns='std').to_csv(OUT/'summary.csv', index=False)
    print(s.round(4).to_string(index=False))


if __name__ == '__main__':
    {'run': run, 'summarise': summarise}[sys.argv[1]]()
