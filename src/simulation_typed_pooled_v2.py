"""Calibrated typed-vs-pooled simulation (v2). Synthetic data only; v1 is kept unchanged.

Changes from v1:
  * Generator parameters come from results/simulation_calibration_v1/calibration.json (original
    three-state panel, no new-states data): mu, h, phi, sigma, omega.
  * Part A (calibrated): ridge over an h grid that includes the calibrated h and its 90% band.
  * Part B (crossover map): ridge over effect size mu x noise sigma x h; reports where typed starts
    to beat pooled, overall and by training length.
  * Part C (tree mechanism): LightGBM with min_child_samples in {2, 5, 10, 20}, by training length.
    A typed flag is on for one day per training year, so it can only be split on once the number of
    training years reaches the leaf minimum.
  * Part D (foundation models, run on Kaggle): Chronos-2 and TimesFM-3 with the pinned weights of the
    registered studies, typed vs pooled flags plus day-of-week covariates, 730-day context, origin =
    event day (lead 1 of a 14-day forecast), h in {0, calibrated, 2}.
Protocol otherwise as v1: event years 2017-2025, training on all earlier days, one-step-ahead with
observed lags, MASE with the weekly-difference scale over up to 730 days before the year.

The design (this file) is committed before any part is run and before the registered new-states
analysis is run.

Run: python src/simulation_typed_pooled_v2.py local
     python src/simulation_typed_pooled_v2.py weights; python src/simulation_typed_pooled_v2.py chronos (or timesfm)
     python src/simulation_typed_pooled_v2.py summarise
"""
import json
import sys
from multiprocessing import Pool
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'results/simulation_typed_pooled_v2'
CAL = json.loads((ROOT/'results/simulation_calibration_v1/calibration.json').read_text())
P0 = {k: CAL[k]['point'] for k in ['mu', 'h', 'phi', 'sigma', 'omega']}
DAYS = pd.date_range('2015-01-01', '2025-12-31')
EVENT_YEARS = list(range(2017, 2026))
BASE_DOY = [70, 110, 245, 280, 310]
Z = np.array([-1.41, -0.71, 0., 0.71, 1.41])
H_GRID = sorted({0., 0.25, round(CAL['h']['lo'], 3), round(P0['h'], 3), round(CAL['h']['hi'], 3), 1., 1.5, 2.})
MU_GRID = [-0.03, -0.06, round(P0['mu'], 4), -0.15]
SIGMA_GRID = [2.0, round(P0['sigma'], 3), 6.0]
LEAVES = [2, 5, 10, 20]
LEAF_H = [0., round(P0['h'], 3), 1., 2.]
FM_H = [0., round(P0['h'], 3), 2.]
REPS = dict(A=200, B=50, C=30, D=10)
LGB = dict(n_estimators=200, learning_rate=0.05, num_leaves=15, verbose=-1, n_jobs=1)
SEED = 20261114


def generate(rng, mu, h, phi, sigma, omega):
    n = len(DAYS)
    doy = DAYS.dayofyear.values
    weekly = np.array([0., -0.01, -0.01, -0.01, -0.01, -0.02, -0.06])[DAYS.dayofweek.values]
    annual = 0.08*np.sin(2*np.pi*doy/365.25) + 0.03*np.cos(4*np.pi*doy/365.25)
    innov = rng.normal(0, sigma, n)
    noise = np.zeros(n)
    for i in range(1, n):
        noise[i] = phi*noise[i-1] + innov[i]
    base = 100*(1 + 0.00002*np.arange(n))*(1 + weekly + annual)
    flags, mult = np.zeros((n, 5)), np.ones(n)
    for y in range(2015, 2026):
        for k, d0 in enumerate(BASE_DOY):
            i = DAYS.get_loc(pd.Timestamp(y, 1, 1) + pd.Timedelta(days=int(d0 + rng.integers(-15, 16)) - 1))
            flags[i, k] = 1.
            mult[i] *= 1 + mu*(1 + h*Z[k]) + omega*abs(mu)*rng.normal()
    return base*mult + noise, flags


def local_X(y, flags):
    doy = DAYS.dayofyear.values
    dow = pd.get_dummies(DAYS.dayofweek).values[:, 1:].astype(float)
    four = np.column_stack([f(2*np.pi*j*doy/365.25) for j in (1, 2, 3) for f in (np.sin, np.cos)])
    base = np.column_stack([dow, four, np.arange(len(y))/len(y), np.r_[np.nan, y[:-1]], np.r_[[np.nan]*7, y[:-7]]])
    pooled = np.column_stack([flags.max(axis=1), np.zeros((len(y), 4))])
    return {'typed': np.column_stack([base, flags]), 'pooled': np.column_stack([base, pooled])}


def scale(y, start):
    a = max(7, start-730)
    return np.mean(np.abs(y[a:start] - y[a-7:start-7]))


def fit_predict(model, leaf, Xtr, ytr, Xte):
    if model == 'ridge':
        from sklearn.linear_model import Ridge
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler
        return make_pipeline(StandardScaler(), Ridge(alpha=1.0)).fit(Xtr, ytr).predict(Xte)
    import lightgbm as lgb
    return lgb.LGBMRegressor(**LGB, min_child_samples=leaf).fit(Xtr, ytr).predict(Xte)


def one(task):
    part, model, leaf, mu, h, sigma, rep = task
    rng = np.random.default_rng([SEED, int(round(-mu*10000)), int(round(h*1000)), int(round(sigma*1000)), rep])
    y, flags = generate(rng, mu, h, P0['phi'], sigma, P0['omega'])
    X = local_X(y, flags)
    rows = []
    for year in EVENT_YEARS:
        start = DAYS.get_loc(pd.Timestamp(year, 1, 1))
        s = scale(y, start)
        tr = np.arange(7, start)
        te = np.where((DAYS.year == year) & (flags.sum(axis=1) > 0))[0]
        err = {arm: np.abs(fit_predict(model, leaf, M[tr], y[tr], M[te]) - y[te])/s for arm, M in X.items()}
        for j, i in enumerate(te):
            rows.append(dict(part=part, model=model, leaf=leaf, mu=mu, h=h, sigma=sigma, rep=rep, year=year,
                             family=int(np.argmax(flags[i])), typed=err['typed'][j], pooled=err['pooled'][j]))
    return rows


def tasks():
    t = {'A': [('A', 'ridge', 0, round(P0['mu'], 4), h, round(P0['sigma'], 3), r) for h in H_GRID for r in range(REPS['A'])],
         'B': [('B', 'ridge', 0, mu, h, s, r) for mu in MU_GRID for s in SIGMA_GRID for h in H_GRID for r in range(REPS['B'])],
         'C': [('C', 'lightgbm', leaf, round(P0['mu'], 4), h, round(P0['sigma'], 3), r) for leaf in LEAVES for h in LEAF_H for r in range(REPS['C'])]}
    return t


def local():
    (OUT/'raw').mkdir(parents=True, exist_ok=True)
    (OUT/'design.json').write_text(json.dumps(dict(seed=SEED, calibration=P0, h_grid=H_GRID, mu_grid=MU_GRID, sigma_grid=SIGMA_GRID,
        leaves=LEAVES, leaf_h=LEAF_H, fm_h=FM_H, reps=REPS, lightgbm=LGB, z=Z.tolist(), base_doy=BASE_DOY), indent=1))
    for part, tl in tasks().items():
        for i in range(0, len(tl), 400):
            f = OUT/'raw'/f'{part}_{i:05d}.csv'
            if f.exists():
                continue
            with Pool(2) as pool:
                parts = pool.map(one, tl[i:i+400])
            pd.DataFrame([r for p in parts for r in p]).to_csv(f, index=False)
            print('done', f.name, flush=True)


def weights():
    import ziel_foundation_v1 as zf
    zf.OUT = OUT
    OUT.mkdir(parents=True, exist_ok=True)
    zf.weights()


def fm(worker):
    import torch
    torch.set_num_threads(2); torch.manual_seed(SEED); np.random.seed(SEED)
    from festival_feature_design import sha
    ident = json.loads((OUT/'weights_identity.json').read_text())
    if worker == 'chronos':
        from chronos import Chronos2Pipeline
        w = next(f for f in ident['chronos']['files'] if f['name'] == 'model.safetensors')
        assert sha(w['path']) == w['sha256']
        model = Chronos2Pipeline.from_pretrained(str(Path(w['path']).parent), device_map='cpu', local_files_only=True)
        median = list(model.quantiles).index(.5)
    else:
        from timesfm3 import TimesFM3Evaluator, ModelConfig
        assert sha(ident['timesfm']['path']) == ident['timesfm']['sha256']
        model = TimesFM3Evaluator(ModelConfig(checkpoint_path=str(Path(ident['timesfm']['path']).parent), device='cpu',
                                              per_core_batch_size=32, local_files_only=True))
    out = OUT/'fm'/worker
    out.mkdir(parents=True, exist_ok=True)
    dow = pd.get_dummies(DAYS.dayofweek).values[:, 1:].astype(np.float32).T
    for h in FM_H:
        f = out/f'h{h}.csv'
        if f.exists():
            continue
        rows = []
        for rep in range(REPS['D']):
            rng = np.random.default_rng([SEED, 999, int(round(h*1000)), rep])
            y, flags = generate(rng, P0['mu'], h, P0['phi'], P0['sigma'], P0['omega'])
            covs = {'typed': np.vstack([dow, flags.T.astype(np.float32)]),
                    'pooled': np.vstack([dow, flags.max(axis=1)[None].astype(np.float32), np.zeros((4, len(y)), np.float32)])}
            ev = [i for i in np.where(flags.sum(axis=1) > 0)[0] if DAYS[i].year in EVENT_YEARS]
            for arm, cov in covs.items():
                inputs = [(y[i-730:i].astype(np.float32), cov[:, i-730:i+14]) for i in ev]
                if worker == 'chronos':
                    packed = [dict(target=t, past_covariates={f'c{j}': c[j, :730] for j in range(len(c))},
                                   future_covariates={f'c{j}': c[j, 730:] for j in range(len(c))}) for t, c in inputs]
                    out_q = model.predict(packed, prediction_length=14, batch_size=128, context_length=730, cross_learning=False)
                    pred = [q[0].detach().cpu().numpy().T[0, median] for q in out_q]
                else:
                    res = list(model.predict_batch([t for t, _ in inputs], horizon=14, past_future_covariates=[c for _, c in inputs],
                                                   return_quantiles=True, use_symmetric_averaging=False))
                    pred = [float(np.asarray(r.forecast).squeeze()[0]) for r in res]
                for i, p in zip(ev, pred):
                    start = DAYS.get_loc(pd.Timestamp(DAYS[i].year, 1, 1))
                    rows.append(dict(part='D', model=worker, h=h, rep=rep, year=DAYS[i].year, family=int(np.argmax(flags[i])),
                                     arm=arm, err=abs(float(p) - y[i])/scale(y, start)))
            print(worker, 'h', h, 'rep', rep, flush=True)
        d = pd.DataFrame(rows)
        d.pivot_table(index=['part', 'model', 'h', 'rep', 'year', 'family'], columns='arm', values='err').reset_index().to_csv(f, index=False)


def crossover(x):
    """Smallest h at which the mean typed-minus-pooled difference crosses below zero (linear interpolation)."""
    x = x.sort_values('h')
    v, hh = x['mean'].values, x.h.values
    for k in range(1, len(v)):
        if v[k-1] >= 0 > v[k]:
            return hh[k-1] + (hh[k]-hh[k-1])*v[k-1]/(v[k-1]-v[k])
    return 0. if v[0] < 0 else np.nan


def summarise():
    d = pd.concat([pd.read_csv(f) for f in sorted((OUT/'raw').glob('*.csv'))], ignore_index=True)
    d['diff'] = d.typed - d.pooled
    d['training'] = np.where(d.year <= 2019, '2-4 years', '5-10 years')
    keys = ['part', 'model', 'leaf', 'mu', 'h', 'sigma']
    rep = d.groupby(keys+['rep'])['diff'].mean()
    s = rep.groupby(keys).agg(['mean', 'std', 'count']).reset_index()
    s['mc_se'] = s['std']/np.sqrt(s['count'])
    s['share_reps_typed_better'] = (rep < 0).groupby(keys).mean().values
    s.drop(columns='std').to_csv(OUT/'summary.csv', index=False)
    cross = s[s.part.isin(['A', 'B'])].groupby(['part', 'mu', 'sigma']).apply(crossover, include_groups=False).rename('h_crossover').reset_index()
    cross.to_csv(OUT/'crossover.csv', index=False)
    leaf = d[d.part == 'C'].groupby(['leaf', 'h', 'year', 'rep'])['diff'].mean().groupby(['leaf', 'h', 'year']).agg(['mean', 'count']).reset_index()
    leaf.to_csv(OUT/'leaf_by_year.csv', index=False)
    fm_files = sorted((OUT/'fm').glob('*/h*.csv'))
    if fm_files:
        f = pd.concat([pd.read_csv(x) for x in fm_files], ignore_index=True)
        f['diff'] = f.typed - f.pooled
        fr = f.groupby(['model', 'h', 'rep'])['diff'].mean()
        fs = fr.groupby(['model', 'h']).agg(['mean', 'std', 'count']).reset_index()
        fs['mc_se'] = fs['std']/np.sqrt(fs['count'])
        fs.drop(columns='std').to_csv(OUT/'summary_fm.csv', index=False)
    figures(s, leaf)
    print(s.round(4).to_string(index=False)); print(cross.round(3).to_string(index=False))


def figures(s, leaf):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 3.6))
    a = s[s.part == 'A']
    ax = axes[0]
    ax.axvspan(CAL['h']['lo'], CAL['h']['hi'], color='0.88', label='calibrated h (90% band)')
    ax.axvline(P0['h'], color='0.5', lw=0.8)
    ax.errorbar(a.h, a['mean'], yerr=1.96*a.mc_se, marker='o', capsize=3, label='ridge')
    fmf = OUT/'summary_fm.csv'
    if fmf.exists():
        f = pd.read_csv(fmf)
        for m, mk in zip(['chronos', 'timesfm'], 'sd'):
            x = f[f.model == m]
            ax.errorbar(x.h, x['mean'], yerr=1.96*x.mc_se, marker=mk, capsize=3, label=m)
    ax.axhline(0, color='grey', lw=0.8)
    ax.set_xlabel('heterogeneity of true effects, h'); ax.set_ylabel('typed minus pooled MASE\n(> 0: pooled better)')
    ax.set_title('Calibrated to three original states'); ax.legend(fontsize=7)
    ax = axes[1]
    x = leaf[leaf.h == round(P0['h'], 3)]
    for lf in LEAVES:
        z = x[x.leaf == lf]
        ax.plot(z.year - 2015, z['mean'], marker='o', label=f'LightGBM min leaf {lf}')
    ax.axhline(0, color='grey', lw=0.8)
    ax.set_xlabel('training years (= days each typed flag is on)'); ax.set_title('Tree leaf minimum, calibrated h')
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(OUT/'simulation_v2.png', dpi=200)


if __name__ == '__main__':
    act = sys.argv[1]
    {'local': local, 'weights': weights, 'summarise': summarise}.get(act, lambda: fm(act))()
