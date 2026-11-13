"""Synthetic study: when do typed event flags beat a pooled flag?

Uses no real data and no results from any registered study. The design (this file and design.json)
is committed before the simulation is run.

Generator (daily, 2015-2025): level 100 with a weak trend, weekly pattern, annual cycle, AR(1) noise.
Five event families, one day each per year, at a lunar-style date (base day of year +/- 15 days, drawn
per year). Each occurrence multiplies demand by (1 + e) with
    e = mu * (1 + h * z_k) + omega * |mu| * eps,   z = (-1.41, -0.71, 0, 0.71, 1.41), eps ~ N(0, 1)
so h controls how different the families' true effects are (h = 0: all identical) and omega adds
occurrence-to-occurrence noise that no flag can explain.

Protocol (mirrors the empirical study): for each event year 2017-2025 a model is trained on all days
before 1 January of that year and forecasts that year's event days one day ahead (lagged values are
the observed ones). Arms: typed (5 family flags) and pooled (one event flag plus 4 zero columns).
Error is MASE with the 730-day weekly-difference scale before the year. The cluster value is the
typed-minus-pooled MASE for each family-year (positive = pooled better).

Run: python src/simulation_typed_pooled_v1.py run    (writes results/simulation_typed_pooled_v1/)
     python src/simulation_typed_pooled_v1.py summarise
"""
import json
import sys
from multiprocessing import Pool
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'results/simulation_typed_pooled_v1'
DAYS = pd.date_range('2015-01-01', '2025-12-31')
EVENT_YEARS = list(range(2017, 2026))
BASE_DOY = [70, 110, 245, 280, 310]
Z = np.array([-1.41, -0.71, 0., 0.71, 1.41])
MU, SIGMA, PHI = -0.06, 2.0, 0.7
H_GRID = [0., 0.25, 0.5, 1., 2.]
OMEGA_GRID = [0., 0.5]
MODELS = {'ridge': 200, 'lightgbm': 50, 'lightgbm_capacity2': 50}   # replications per setting
LGB = dict(n_estimators=200, learning_rate=0.05, num_leaves=15, subsample=1.0, colsample_bytree=1.0, verbose=-1, n_jobs=1)
SEED = 20261114


def generate(rng, h, omega):
    n = len(DAYS)
    t = np.arange(n)
    doy = DAYS.dayofyear.values
    weekly = np.array([0., -0.01, -0.01, -0.01, -0.01, -0.02, -0.06])[DAYS.dayofweek.values]
    annual = 0.08*np.sin(2*np.pi*doy/365.25) + 0.03*np.cos(4*np.pi*doy/365.25)
    noise = np.zeros(n)
    innov = rng.normal(0, SIGMA, n)
    for i in range(1, n):
        noise[i] = PHI*noise[i-1] + innov[i]
    base = 100*(1 + 0.00002*t)*(1 + weekly + annual)
    flags = np.zeros((n, 5))
    mult = np.ones(n)
    for y in range(2015, 2026):
        for k, d0 in enumerate(BASE_DOY):
            day = pd.Timestamp(y, 1, 1) + pd.Timedelta(days=int(d0 + rng.integers(-15, 16)) - 1)
            i = DAYS.get_loc(day)
            flags[i, k] = 1.
            mult[i] *= 1 + MU*(1 + h*Z[k]) + omega*abs(MU)*rng.normal()
    return base*mult + noise, flags


def design_matrix(y, flags):
    doy = DAYS.dayofyear.values
    dow = pd.get_dummies(DAYS.dayofweek).values[:, 1:].astype(float)
    four = np.column_stack([f(2*np.pi*j*doy/365.25) for j in (1, 2, 3) for f in (np.sin, np.cos)])
    lag1 = np.r_[np.nan, y[:-1]]
    lag7 = np.r_[[np.nan]*7, y[:-7]]
    trend = np.arange(len(y))/len(y)
    base = np.column_stack([dow, four, trend, lag1, lag7])
    pooled = np.column_stack([flags.max(axis=1), np.zeros((len(y), 4))])
    return {'typed': np.column_stack([base, flags]), 'pooled': np.column_stack([base, pooled])}


def fit_predict(model, Xtr, ytr, Xte):
    if model == 'ridge':
        from sklearn.linear_model import Ridge
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler
        return make_pipeline(StandardScaler(), Ridge(alpha=1.0)).fit(Xtr, ytr).predict(Xte)
    import lightgbm as lgb
    params = dict(LGB, min_child_samples=2 if model == 'lightgbm_capacity2' else 20)
    return lgb.LGBMRegressor(**params).fit(Xtr, ytr).predict(Xte)


def one(task):
    model, h, omega, rep = task
    rng = np.random.default_rng([SEED, int(h*100), int(omega*100), rep])
    y, flags = generate(rng, h, omega)
    X = design_matrix(y, flags)
    rows = []
    for year in EVENT_YEARS:
        start = DAYS.get_loc(pd.Timestamp(year, 1, 1))
        a = max(7, start-730)   # 2017 has only 724 usable weekly differences
        scale = np.mean(np.abs(y[a:start] - y[a-7:start-7]))
        tr = np.arange(7, start)
        te = np.where((DAYS.year == year) & (flags.sum(axis=1) > 0))[0]
        err = {}
        for arm, M in X.items():
            p = fit_predict(model, M[tr], y[tr], M[te])
            err[arm] = np.abs(p - y[te])/scale
        for j, i in enumerate(te):
            rows.append(dict(model=model, h=h, omega=omega, rep=rep, year=year, family=int(np.argmax(flags[i])),
                             typed=err['typed'][j], pooled=err['pooled'][j]))
    return rows


def design():
    return dict(seed=SEED, mu=MU, sigma=SIGMA, phi=PHI, z=Z.tolist(), base_doy=BASE_DOY, h_grid=H_GRID, omega_grid=OMEGA_GRID,
                replications=MODELS, lightgbm=LGB, event_years=EVENT_YEARS, days=[str(DAYS[0].date()), str(DAYS[-1].date())])


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/'design.json').write_text(json.dumps(design(), indent=1))
    for model, reps in MODELS.items():
        for omega in OMEGA_GRID:
            for h in H_GRID:
                f = OUT/'raw'/f'{model}_h{h}_omega{omega}.csv'
                if f.exists():
                    continue
                f.parent.mkdir(exist_ok=True)
                with Pool(2) as pool:
                    parts = pool.map(one, [(model, h, omega, r) for r in range(reps)])
                pd.DataFrame([r for p in parts for r in p]).to_csv(f, index=False)
                print('done', f.name, flush=True)


def summarise():
    d = pd.concat([pd.read_csv(f) for f in sorted((OUT/'raw').glob('*.csv'))], ignore_index=True)
    d['diff'] = d.typed - d.pooled
    rep = d.groupby(['model', 'omega', 'h', 'rep'])['diff'].mean()
    s = rep.groupby(['model', 'omega', 'h']).agg(typed_minus_pooled='mean', sd='std', reps='count')
    s['mc_se'] = s.sd/np.sqrt(s.reps)
    s['share_reps_typed_better'] = (rep < 0).groupby(['model', 'omega', 'h']).mean()
    s = s.drop(columns='sd').reset_index()
    s.to_csv(OUT/'summary.csv', index=False)
    early = d.year <= 2019
    by_n = d.assign(training=np.where(early, '2-4 years', '5-10 years')).groupby(['model', 'omega', 'h', 'training', 'rep'])['diff'].mean() \
            .groupby(['model', 'omega', 'h', 'training']).agg(['mean', 'count']).reset_index()
    by_n.to_csv(OUT/'summary_by_training_length.csv', index=False)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.4), sharey=True)
    for ax, omega in zip(axes, OMEGA_GRID):
        for model, mk in zip(MODELS, 'osd'):
            x = s[(s.model == model) & (s.omega == omega)]
            ax.errorbar(x.h, x.typed_minus_pooled, yerr=1.96*x.mc_se, marker=mk, capsize=3, label=model)
        ax.axhline(0, color='grey', lw=0.8)
        ax.set_xlabel('heterogeneity of true effects, h')
        ax.set_title(f'occurrence noise omega = {omega}')
    axes[0].set_ylabel('typed minus pooled MASE\n(> 0: pooled better)')
    axes[0].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT/'typed_vs_pooled_simulation.png', dpi=200)
    print(s.round(4).to_string(index=False))


if __name__ == '__main__':
    {'run': run, 'summarise': summarise}[sys.argv[1]]()
