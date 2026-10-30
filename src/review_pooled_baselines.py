"""Bounded clean-environment scalar reproduction; no project model helpers.

This is another internal implementation by the same assistant, not human review.
First2024event target per state is chosen from dates, without looking at errors.
"""
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import sys
import numpy as np
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from lightgbm import LGBMRegressor

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'results/pooled_festival_v1'
ARMS = ['pooled_day1', 'pooled_day5', 'pooled_window1', 'pooled_window5', 'zero1']


def main():
    destination = OUT/'clean_scalar_review.json'
    if destination.exists():
        raise FileExistsError('Preserve prior review, including discrepancies')
    data = pd.read_csv(ROOT/'data/external/latest_state_energy_GWh.csv', index_col=0, parse_dates=True).asfreq('D')
    cases = pd.read_csv(OUT/'event/primary_cases.csv', parse_dates=['date', 'origin'])
    ledger = pd.read_csv(ROOT/'results/festival_features_v1/anchors_2022_2025.csv', parse_dates=['date'])
    checks, matrix_checks = [], []
    for state in ['Delhi', 'Karnataka', 'Maharashtra']:
        raw = data[state].where(data[state] > 0)
        values = raw.to_numpy(copy=True)
        for i in range(len(values)):
            if not np.isfinite(values[i]):
                values[i] = values[i-7] if i >= 7 and np.isfinite(values[i-7]) else values[i-1] if i else np.nan
        history = pd.Series(values, index=data.index)
        anchors = set(ledger[ledger.state.eq(state)].date)
        windows = {d for a in anchors for d in pd.date_range(a-pd.Timedelta(days=3), a+pd.Timedelta(days=3))}
        first = cases[cases.state.eq(state) & cases.year.eq(2024)].date.min()
        for h in [1, 7, 14]:
            origin = first-pd.Timedelta(days=h-1)
            cutoff = origin.replace(day=1)-pd.Timedelta(days=1)
            origins = pd.date_range(cutoff-pd.Timedelta(days=729), cutoff-pd.Timedelta(days=h-1))

            def row(o):
                target = o+pd.Timedelta(days=h-1)
                a = [history.at[o-pd.Timedelta(days=k)] for k in [1, 2, 3, 7, 14, 21, 28, 56, 364, 365, 366]]
                means = {}
                for width in [7, 28, 56]:
                    z = history.loc[o-pd.Timedelta(days=width):o-pd.Timedelta(days=1)].to_numpy()
                    means[width] = z.mean()
                    a += [z.mean(), z.std(ddof=1), z.min(), z.max()]
                a += [means[7]-means[28]]
                a += [history.at[target-pd.Timedelta(days=k)] for k in [364, 365, 366]]
                a += [float(target.dayofweek == k) for k in range(7)]
                for k in [1, 2, 3]:
                    angle = 2*np.pi*k*target.dayofyear/365.2425
                    a += [np.sin(angle), np.cos(angle)]
                return a

            base = np.asarray([row(o) for o in origins], dtype=float)
            query = np.asarray(row(origin), dtype=float)
            target_dates = origins+pd.Timedelta(days=h-1)
            y = raw.reindex(target_dates).to_numpy()
            valid = np.isfinite(y) & np.isfinite(base).all(axis=1)
            for worker in ['ridge', 'lightgbm', 'lightgbm_capacity2']:
                older = 'strong_refit_v1' if worker == 'ridge' else 'stable_tree_refit_v2'
                old = ROOT/'results'/older
                selected = pd.read_csv(old/'selected.csv')
                model_name = 'ridge' if worker == 'ridge' else 'lightgbm'
                choice = selected[selected.state.eq(state) & selected.year.eq(2024) & selected.model.eq(model_name) & selected['mode'].eq('rich_calendar') & selected.horizon.eq(h)]
                assert len(choice) == 1
                params = json.loads(choice.parameters.iloc[0])
                if worker == 'lightgbm_capacity2':
                    params['min_child_samples'] = 2
                fixed = json.loads((old/'protocol.json').read_text())
                predictions = pd.read_csv(OUT/'event'/worker/'predictions.csv', parse_dates=['origin'])
                fitlog = json.loads((OUT/'event'/worker/'fit_log.json').read_text())
                for arm in ARMS:
                    width = 5 if arm.endswith('5') else 1
                    active = windows if 'window' in arm else anchors
                    flags = np.zeros(len(origins)) if arm == 'zero1' else target_dates.isin(active).astype(float)
                    extras = np.column_stack([flags]+[np.zeros(len(origins)) for _ in range(width-1)])
                    query_flag = 0. if arm == 'zero1' else float(first in active)
                    xx = np.column_stack([base, extras])[valid]
                    q = np.concatenate([query, [query_flag]+[0.]*(width-1)])[None, :]
                    if worker != 'ridge':
                        xx = xx.astype(np.float32); q = q.astype(np.float32)
                    model = make_pipeline(StandardScaler(), Ridge(**params)) if worker == 'ridge' else LGBMRegressor(**params, **fixed['lightgbm_fixed'])
                    point = float(model.fit(xx, y[valid]).predict(q)[0])
                    recorded = predictions[predictions.state.eq(state) & predictions.origin.eq(origin) & predictions.horizon.eq(h) & predictions.arm.eq(arm)]
                    assert len(recorded) == 1
                    saved = float(recorded.prediction.iloc[0]); delta = abs(point-saved)
                    checks.append(dict(state=state, year=2024, origin=str(origin.date()), target=str(first.date()), horizon=h,
                        model=worker, arm=arm, absolute_difference_GWh=delta,
                        matches=bool(np.isclose(point, saved, rtol=1e-7, atol=1e-6))))
                    log = [r for r in fitlog if r['state'] == state and r['year'] == 2024 and r['horizon'] == h and r['arm'] == arm and r['refit'] == str((cutoff+pd.Timedelta(days=1)).date())]
                    assert len(log) == 1
                    matrix_checks.append(dict(state=state, horizon=h, model=worker, arm=arm,
                        exact_training_X=hashlib.sha256(xx.tobytes()).hexdigest() == log[0]['training_X_sha256'],
                        exact_y=hashlib.sha256(y[valid].tobytes()).hexdigest() == log[0]['training_y_sha256']))
            print(state, h, 'scalar review complete', flush=True)
    passed = all(r['matches'] for r in checks) and all(r['exact_y'] for r in matrix_checks)
    # Tiny float64 rolling differences are expected; tree contracts must match.
    passed = passed and all(r['exact_training_X'] for r in matrix_checks if r['model'] != 'ridge')
    result = dict(status='pass' if passed else 'discrepancies_retained', completed_utc=datetime.now(timezone.utc).isoformat(),
        scope='First2024event date per state,3leads,5newarms,3regression variants; separate scalar histories/feature construction in clean environment. Not all forecasts, foundation inference or human review.',
        python=platform.python_version(), interpreter=str(Path(sys.executable)),
        packages={name: importlib.metadata.version(name) for name in ['numpy', 'pandas', 'scipy', 'scikit-learn', 'lightgbm']},
        forecast_checks=len(checks), max_difference_GWh=max(r['absolute_difference_GWh'] for r in checks),
        checks=checks, matrix_checks=matrix_checks,
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    destination.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ['checks', 'matrix_checks']}, indent=2))
    if not passed:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
