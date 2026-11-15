"""SARIMAX in the pipeline-matched simulation (EXPLORATORY; after the registered analysis; design committed before running).

SARIMAX is the model of the confirmed H1 but was not in the earlier simulations. This mirrors the registered specification
(src/breadth_model_engine_v1.sarimax): for each event year, one fit on the 730 days ending 31 December of the previous year,
SARIMAX(1,0,0)(1,0,0,7), no trend, exogenous calendar regressors plus the arm's flags, y scaled by 1/100; the fitted
parameters are then kept fixed and the model is run forward through the year (lead-1 forecasts = one-step predictions with
fixed parameters and observed history). Calendar regressors in the simulation: annual Fourier terms (3 pairs); weekly
structure is left to the seasonal AR term, as in the registered model. Generator: simulation_typed_pooled_v3 (window
profile; all days of the +-3-day windows scored).
  Part 1: three-state calibration, h in {0, 0.25, 0.462, 1, 2}, 20 replications.
  Part 2: each further state with its own 2015-2020 parameters, 20 replications, compared with observed 2021-2025 SARIMAX.
Run: python src/simulation_sarimax_v3.py
"""
import json
import sys
import warnings
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

OUT = ROOT/'results/simulation_sarimax_v3'
H_GRID = [0., 0.25, 0.462, 1., 2.]
REPS, SEED = 20, 20261117
P_CAL = dict(s3.P0)


def exog(flags, arm):
    doy = s3.DAYS.dayofyear.values
    four = np.column_stack([f(2*np.pi*j*doy/365.25) for j in (1, 2, 3) for f in (np.sin, np.cos)])
    fl = flags if arm == 'typed' else flags.max(axis=1, keepdims=True)
    return np.column_stack([four, fl])


def one(task):
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    warnings.filterwarnings('ignore')
    label, params, h, rep = task
    s3.P0 = dict(params)
    rng = np.random.default_rng([SEED, zlib.crc32(label.encode()) % 10**6, int(round(h*1000)), rep])
    y, flags, window = s3.generate(rng, h)
    yy = y/100.
    diffs = []
    for year in s3.EVENT_YEARS:
        start = s3.DAYS.get_loc(pd.Timestamp(year, 1, 1))
        end = s3.DAYS.get_loc(pd.Timestamp(year, 12, 31))
        sc = s2.scale(y, start)
        te = np.where((s3.DAYS.year == year) & window)[0]
        err = {}
        for arm in ['typed', 'pooled']:
            X = exog(flags, arm)
            tr = slice(start-730, start)
            fit = SARIMAX(yy[tr], exog=X[tr], order=(1, 0, 0), seasonal_order=(1, 0, 0, 7), trend='n',
                          enforce_stationarity=False).fit(disp=False)
            full = SARIMAX(yy[start-730:end+1], exog=X[start-730:end+1], order=(1, 0, 0), seasonal_order=(1, 0, 0, 7), trend='n',
                           enforce_stationarity=False).filter(fit.params)
            pred = np.asarray(full.get_prediction(start=730).predicted_mean)*100.   # one-step-ahead, fixed parameters
            p = pred[te - start]
            err[arm] = np.abs(p - y[te])/sc
        diffs.append(float(np.mean(err['typed']) - np.mean(err['pooled'])))
    return dict(label=label, h=h, rep=rep, typed_minus_pooled=float(np.mean(diffs)))


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    cal = pd.read_csv(ROOT/'results/simulation_calibration_v3_timesplit/calibration_2015_2020.csv')
    tasks = [('three-state calibration', P_CAL, h, r) for h in H_GRID for r in range(REPS)]
    for r in cal.itertuples():
        tasks += [(r.state, dict(mu=r.mu, h=r.h, phi=r.phi, sigma=r.sigma, omega=r.omega), round(float(r.h), 3), k) for k in range(REPS)]
    (OUT/'design.json').write_text(json.dumps(dict(h_grid=H_GRID, reps=REPS, seed=SEED, calibration=P_CAL,
                                                   specification='SARIMAX(1,0,0)(1,0,0,7), no trend, Fourier(3) + flags, 730-day fit per year, fixed parameters'), indent=1))
    with Pool(2) as pool:
        d = pd.DataFrame(pool.map(one, tasks))
    d.to_csv(OUT/'raw.csv', index=False)
    s = d.groupby(['label', 'h']).typed_minus_pooled.agg(['mean', 'std', 'count']).reset_index()
    s['mc_se'] = s['std']/np.sqrt(s['count'])
    s.drop(columns='std').to_csv(OUT/'summary.csv', index=False)
    obs = c2.observed_years(range(2021, 2026))
    obs = obs[obs.model == 'sarimax'][['state', 'observed_typed_minus_pooled']]
    st = s[s.label != 'three-state calibration'].rename(columns={'label': 'state', 'mean': 'predicted_sarimax'})[['state', 'h', 'predicted_sarimax', 'mc_se']]
    st = st.merge(obs, on='state')
    st.to_csv(OUT/'per_state_predicted_vs_observed_2021_2025.csv', index=False)
    from scipy import stats
    r1, r2 = stats.pearsonr(st.predicted_sarimax, st.observed_typed_minus_pooled), stats.spearmanr(st.predicted_sarimax, st.observed_typed_minus_pooled)
    (OUT/'summary.json').write_text(json.dumps(dict(pearson=r1.statistic, pearson_p=r1.pvalue, spearman=r2.statistic, spearman_p=r2.pvalue,
                                                    mean_predicted=float(st.predicted_sarimax.mean()), mean_observed=float(st.observed_typed_minus_pooled.mean())), indent=1))
    print(s.round(4).to_string(index=False)); print(st.round(4).to_string(index=False))


if __name__ == '__main__':
    main()
