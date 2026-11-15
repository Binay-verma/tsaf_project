"""Leaf-size experiment (EXPLORATORY; prediction committed before any run): LightGBM minimum leaf size and typed flags.

For both registered new-states tests (results/new_states_v1 and results/new_states_v2), lead 1 only, the registered
LightGBM pipeline is rerun with every selected parameter kept except min_child_samples, set to L in LEAVES, for the
calendar, typed-day (day5) and pooled-day (pooled_day5) arms. Same cases, frames, monthly refits, 730-day windows
and scales as the registered runs. Nothing registered is changed or overwritten.

Per fit it records how many training rows each typed flag and the pooled flag are set on, and whether the typed
arm's predictions equal the calendar arm's exactly. Prediction: results/leaf_size_experiment_v1/PREDICTION.md.

Run (each test in its own process, because the study modules redirect the shared state list):
  python src/leaf_size_experiment_v1.py v1
  python src/leaf_size_experiment_v1.py v2
"""
import importlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd

TEST = sys.argv[1]
assert TEST in ('v1', 'v2')
study = importlib.import_module('new_states_v1' if TEST == 'v1' else 'new_states_v2')   # patches forecasting first
import longer_panel_stage_a_v1 as A  # noqa: E402
from robust_baselines import design_frame, fitting_cases, make_model  # noqa: E402
import breadth_model_engine_v1 as engine  # noqa: E402
from festival_feature_design import sha, dump  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/f'results/new_states_{TEST}'
OUT = ROOT/'results/leaf_size_experiment_v1'/TEST
LEAVES = [1, 2, 3, 4, 5, 6, 8, 10, 20]
ARMS = ['calendar', 'day5', 'pooled_day5']


def main():
    assert (ROOT/'results/leaf_size_experiment_v1/PREDICTION.md').exists(), 'commit the prediction first'
    OUT.mkdir(parents=True, exist_ok=False)
    dump(OUT/'started.json', dict(started_utc=datetime.now(timezone.utc).isoformat(), leaves=LEAVES, arms=ARMS,
                                  inputs={str(p.relative_to(ROOT)): sha(p) for p in [BASE/'anchors_2015_2025.csv', BASE/'placebo_anchors_2015_2025.csv',
                                          BASE/'event_window/primary_cases.csv', Path(str(BASE)+'_selection_tree')/'selected.csv', Path(__file__)]}))
    cases = pd.read_csv(BASE/'event_window/primary_cases.csv', parse_dates=['origin', 'date'])
    cases = cases[cases.horizon == 1]
    data = study.load_new()
    a = pd.read_csv(BASE/'anchors_2015_2025.csv'); fake = pd.read_csv(BASE/'placebo_anchors_2015_2025.csv')
    sel = pd.read_csv(Path(str(BASE)+'_selection_tree')/'selected.csv')
    fixed = json.loads((ROOT/'results/stable_tree_refit_v2/protocol.json').read_text())
    rows, fits = [], []
    for (state, year), group in cases.groupby(['state', 'year']):
        observed = data[state]; fc = A.frames(data.index, state, a, fake)
        base, _ = design_frame(observed, state, 1, 'rich_calendar')
        cal = list(fc['calendar'].columns)
        chosen = sel[sel.state.eq(state) & sel.year.eq(year) & sel.horizon.eq(1) & sel['mode'].eq('rich_calendar') & sel.model.eq('lightgbm')]
        assert len(chosen) == 1
        params0 = json.loads(chosen.parameters.iloc[0])
        X = {}
        for arm in ARMS:
            sh = fc[arm].reindex(data.index).copy(); sh.index = data.index
            x = base.copy(); x[cal] = sh.iloc[:, :13].to_numpy(); x = pd.concat([x, sh.iloc[:, 13:]], axis=1)
            X[arm] = x.astype(np.float32)
        typed_cols = [c for c in X['day5'].columns if c.endswith('_day') and c in fc['day5'].columns[13:]]
        for month, seg in group.groupby(group.origin.dt.to_period('M')):
            refit = pd.Timestamp(month.start_time); cutoff = refit-pd.Timedelta(days=1)
            study.bound([cutoff-pd.Timedelta(days=729), cutoff, seg.date.min(), seg.date.max()])
            pre = {}
            for arm in ARMS:
                xx, yy, log = fitting_cases(X[arm], observed, 1, cutoff)
                assert pd.Timestamp(log['training_target_max']) < refit <= seg.origin.min()
                pre[arm] = (xx, yy, X[arm].reindex(pd.DatetimeIndex(seg.origin)).to_numpy())
            cols = list(X['day5'].columns)
            counts = {c: int(pre['day5'][0][:, cols.index(c)].sum()) for c in typed_cols}
            pcols = list(X['pooled_day5'].columns)
            pooled_count = int(pre['pooled_day5'][0][:, pcols.index('event_day')].sum())
            for L in LEAVES:
                params = dict(params0, min_child_samples=L)
                pred = {}
                for arm in ARMS:
                    xx, yy, q = pre[arm]
                    pred[arm] = make_model('lightgbm', params, fixed).fit(xx, yy).predict(q)
                    s = seg.copy(); s['prediction'] = pred[arm]; s['mase_scale'] = engine.scale(data, state, int(year))
                    s['leaf'] = L; s['arm'] = arm; rows.append(s)
                fits.append(dict(state=state, year=int(year), refit=str(refit.date()), leaf=L, selected_leaf=params0.get('min_child_samples'),
                                 typed_max_count=max(counts.values()) if counts else 0, typed_counts=counts, pooled_count=pooled_count,
                                 typed_equals_calendar=bool(np.array_equal(pred['day5'], pred['calendar'])),
                                 pooled_equals_calendar=bool(np.array_equal(pred['pooled_day5'], pred['calendar']))))
        print(TEST, state, year, flush=True)
    d = pd.concat(rows, ignore_index=True)
    d.to_csv(OUT/'predictions.csv', index=False)
    pd.DataFrame(fits).to_json(OUT/'fits.json', orient='records', indent=1)
    dump(OUT/'run.json', dict(completed_utc=datetime.now(timezone.utc).isoformat(), rows=len(d), fits=len(fits),
                              predictions_sha256=sha(OUT/'predictions.csv')))


if __name__ == '__main__':
    main()
