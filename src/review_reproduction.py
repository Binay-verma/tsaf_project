"""Separate baseline implementation for a bounded clean-environment review.

Imports no forecasting/feature/model functions from the application. This is a
software reproduction check by the same assistant, not independent peer review.
"""
from pathlib import Path
import hashlib
import importlib.metadata
import json
import platform
import argparse
import numpy as np
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from lightgbm import LGBMRegressor

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'results/provenance_review_v1'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--experiment', default='strong_refit_v1')
    parser.add_argument('--contract', choices=['float64', 'float32'], default='float64')
    args = parser.parse_args()
    result_dir = ROOT/'results'/args.experiment
    data = pd.read_csv(ROOT/'data/external/latest_state_energy_GWh.csv', index_col=0, parse_dates=True)
    observed = data.Karnataka.where(data.Karnataka > 0).asfreq('D')
    vals = observed.to_numpy(copy=True)
    for i in range(len(vals)):
        if not np.isfinite(vals[i]):
            vals[i] = vals[i-7] if i >= 7 and np.isfinite(vals[i-7]) else vals[i-1] if i else np.nan
    history = pd.Series(vals, index=observed.index)
    config = json.loads((result_dir/'protocol.json').read_text())
    selected = pd.read_csv(result_dir/'selected.csv')
    saved = pd.read_csv(result_dir/'predictions.csv', parse_dates=['origin'])
    checks, searches = [], []
    for horizon in [1, 7, 14]:
        def row(origin):
            target = origin+pd.Timedelta(days=horizon-1)
            values = [history.at[origin-pd.Timedelta(days=k)] for k in [1,2,3,7,14,21,28,56,364,365,366]]
            means = {}
            for window in [7, 28, 56]:
                a = history.loc[origin-pd.Timedelta(days=window):origin-pd.Timedelta(days=1)].to_numpy()
                means[window] = a.mean()
                values += [a.mean(), a.std(ddof=1), a.min(), a.max()]
            values += [means[7]-means[28]]
            values += [history.at[target-pd.Timedelta(days=k)] for k in [364,365,366]]
            values += [float(target.dayofweek == k) for k in range(7)]
            for k in [1,2,3]:
                angle = 2*np.pi*k*target.dayofyear/365.2425
                values += [np.sin(angle), np.cos(angle)]
            return np.asarray(values, dtype=np.float32 if args.contract == 'float32' else float)
        def dataset(cutoff):
            origins = pd.date_range(cutoff-pd.Timedelta(days=729), cutoff-pd.Timedelta(days=horizon-1))
            x = np.vstack([row(o) for o in origins])
            y = observed.reindex(origins+pd.Timedelta(days=horizon-1)).to_numpy()
            mask = np.isfinite(y) & np.isfinite(x).all(axis=1)
            cache = Path('/workspace/review-matrix-cache')
            if args.contract == 'float32':
                cache = cache/'float32'
            cache.mkdir(exist_ok=True, parents=True)
            np.savez(cache/f'h{horizon}_{cutoff.date()}.npz', x=x[mask], y=y[mask])
            return x[mask], y[mask]
        validation_origins = pd.date_range('2025-07-05', pd.Timestamp('2025-12-31')-pd.Timedelta(days=horizon-1))
        vx = np.vstack([row(o) for o in validation_origins])
        vy = observed.reindex(validation_origins+pd.Timedelta(days=horizon-1)).to_numpy()
        x, y = dataset(pd.Timestamp('2025-07-04'))
        for model_name in config['models']:
            grid = [dict(alpha=a) for a in config['ridge_alphas']] if model_name == 'ridge' else config['lightgbm_grid']
            def fit(params, x, y):
                if model_name == 'ridge':
                    return make_pipeline(StandardScaler(), Ridge(**params)).fit(x, y)
                return LGBMRegressor(**params, **{**config['lightgbm_fixed'], 'n_jobs': 1}).fit(x, y)
            losses = [float(np.mean(abs(vy-fit(params, x, y).predict(vx)))) for params in grid]
            chosen = int(np.argmin(losses))
            recorded = selected[selected.state.eq('Karnataka') & selected.year.eq(2026) &
                selected['mode'].eq('rich_calendar') & selected.model.eq(model_name) & selected.horizon.eq(horizon)].iloc[0]
            searches.append(dict(model=model_name, horizon=horizon, chosen=chosen,
                recorded=int(recorded.configuration), selected_matches=bool(chosen == recorded.configuration),
                loss_matches=bool(np.isclose(losses[chosen], recorded.MAE, rtol=1e-7, atol=1e-7)),
                max_selected_loss_difference=abs(losses[chosen]-recorded.MAE)))
            for schedule, origin in [('annual', pd.Timestamp('2026-01-01')),
                                     ('annual', pd.Timestamp('2026-10-15')),
                                     ('monthly', pd.Timestamp('2026-05-15')),
                                     ('monthly', pd.Timestamp('2026-10-15'))]:
                cutoff = pd.Timestamp('2025-12-31') if schedule == 'annual' else origin.replace(day=1)-pd.Timedelta(days=1)
                xx, yy = dataset(cutoff)
                prediction = float(fit(grid[chosen], xx, yy).predict(row(origin)[None, :])[0])
                a = saved[saved.state.eq('Karnataka') & saved.year.eq(2026) & saved['mode'].eq('rich_calendar') &
                          saved.model.eq(model_name) & saved.horizon.eq(horizon) & saved.schedule.eq(schedule) & saved.origin.eq(origin)]
                assert len(a) == 1
                delta = abs(prediction-float(a.prediction.iloc[0]))
                checks.append(dict(model=model_name, horizon=horizon, schedule=schedule,
                    origin=str(origin.date()), absolute_difference=delta,
                    matches=bool(np.isclose(prediction, a.prediction.iloc[0], rtol=1e-7, atol=1e-6))))
    passed = all(c['matches'] for c in checks) and all(c['selected_matches'] and c['loss_matches'] for c in searches)
    info = dict(status='passed' if passed else 'discrepancies_retained', python=platform.python_version(),
        experiment=args.experiment, feature_contract=args.contract,
        interpreter=str(Path(__import__('sys').executable)), inherited_system_packages=False,
        selected_configurations_reproduced=len(searches), forecast_checks=len(checks),
        max_forecast_difference=max(c['absolute_difference'] for c in checks),
        scope='Karnataka2026, rich_calendar, three leads, annual/monthly examples; not all forecasts or human review',
        packages={p: importlib.metadata.version(p) for p in ['numpy','pandas','scikit-learn','lightgbm','scipy']},
        searches=searches, forecasts=checks,
        code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    filename = ('separate_implementation_review.json' if args.contract == 'float64'
                else 'separate_implementation_review_float32.json')
    (OUT/filename).write_text(json.dumps(info, indent=2)+'\n')
    print(json.dumps({k:v for k,v in info.items() if k not in ['searches','forecasts']}, indent=2))
    if not passed:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
