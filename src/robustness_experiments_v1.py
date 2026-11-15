"""Robustness experiments after both registered new-states tests (EXPLORATORY; predictions committed before any run).

Lead 1, both tests (results/new_states_v1 and _v2), the registered rich-history design, frames, monthly refits and
scales; selected parameters from the registered pre-year selections. Nothing registered is changed or overwritten.

Experiments (results/robustness_experiments_v1/<test>/<experiment>/predictions.csv):
  window       training window W in {730, 1460, 2190} days, event years 2021-2025 (the ledger starts in 2015, so the
               longest window is fully covered); models ridge, lgbm_leaf2, lgbm_selected; arms calendar, day5,
               pooled_day5, hybrid (typed flags plus the pooled flag).
  noise        W = 730, 2017-2025; each anchor row moved by one day (random sign) with probability 0.2, seeds 1 and 2,
               the same moved ledger for typed and pooled; models ridge, lgbm_leaf2; arms day5, pooled_day5.
  ridge_alpha  W = 730, 2017-2025; Ridge with alpha in {0.1, 1, 10, 100, 1000} for every arm (calendar, day5,
               pooled_day5, hybrid) instead of the selected alpha.
Prediction: results/robustness_experiments_v1/PREDICTION.md.
Run: python src/robustness_experiments_v1.py v1|v2 window|noise|ridge_alpha
"""
import importlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd

TEST, EXP = sys.argv[1], sys.argv[2]
assert TEST in ('v1', 'v2') and EXP in ('window', 'noise', 'ridge_alpha')
study = importlib.import_module('new_states_v1' if TEST == 'v1' else 'new_states_v2')   # patches forecasting first
import longer_panel_stage_a_v1 as A  # noqa: E402
from robust_baselines import design_frame, fitting_cases, make_model  # noqa: E402
import breadth_model_engine_v1 as engine  # noqa: E402
from festival_feature_design import sha, dump  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/f'results/new_states_{TEST}'
OUT = ROOT/'results/robustness_experiments_v1'/TEST/EXP
FIXED = json.loads((ROOT/'results/stable_tree_refit_v2/protocol.json').read_text())


def hybrid(fc):
    t = fc['day5']; p = fc['pooled_day5']
    return pd.concat([t, p[['event_day']]], axis=1)


def moved(a, seed, q=0.2):
    rng = np.random.default_rng(seed)
    a = a.copy()
    move = rng.random(len(a)) < q
    sign = rng.choice([-1, 1], size=len(a))
    d = pd.to_datetime(a.date) + pd.to_timedelta(np.where(move, sign, 0), unit='D')
    a['date'] = d.dt.strftime('%Y-%m-%d'); a['moved'] = move
    return a


def configs():
    if EXP == 'window':
        return [dict(W=W, model=m, arms=['calendar', 'day5', 'pooled_day5', 'hybrid'], ledger='registered')
                for W in (730, 1460, 2190) for m in ('ridge', 'lgbm_leaf2', 'lgbm_selected')]
    if EXP == 'noise':
        return [dict(W=730, model=m, arms=['day5', 'pooled_day5'], ledger=f'moved_seed{s}') for s in (1, 2) for m in ('ridge', 'lgbm_leaf2')]
    return [dict(W=730, model=f'ridge_alpha{al:g}', arms=['calendar', 'day5', 'pooled_day5', 'hybrid'], ledger='registered')
            for al in (0.1, 1, 10, 100, 1000)]


def main():
    assert (ROOT/'results/robustness_experiments_v1/PREDICTION.md').exists(), 'commit the prediction first'
    OUT.mkdir(parents=True, exist_ok=False)
    years = list(range(2021, 2026)) if EXP == 'window' else list(range(2017, 2026))
    cases = pd.read_csv(BASE/'event_window/primary_cases.csv', parse_dates=['origin', 'date'])
    cases = cases[(cases.horizon == 1) & cases.year.isin(years)]
    data = study.load_new()
    a0 = pd.read_csv(BASE/'anchors_2015_2025.csv'); fake = pd.read_csv(BASE/'placebo_anchors_2015_2025.csv')
    ledgers = {'registered': a0, 'moved_seed1': moved(a0, 1), 'moved_seed2': moved(a0, 2)}
    for k in ('moved_seed1', 'moved_seed2'):
        ledgers[k].to_csv(OUT/f'ledger_{k}.csv', index=False)
    sel_r = pd.read_csv(Path(str(BASE)+'_selection_ridge')/'selected.csv')
    sel_t = pd.read_csv(Path(str(BASE)+'_selection_tree')/'selected.csv')
    dump(OUT/'started.json', dict(started_utc=datetime.now(timezone.utc).isoformat(), configs=configs(), years=years,
                                  script_sha256=sha(Path(__file__))))
    rows, fits = [], []
    for (state, year), group in cases.groupby(['state', 'year']):
        observed = data[state]
        base, _ = design_frame(observed, state, 1, 'rich_calendar')
        frames = {}
        for name, led in ledgers.items():
            if EXP != 'noise' and name != 'registered':
                continue
            fc = A.frames(data.index, state, led, fake); fc['hybrid'] = hybrid(fc)
            cal = list(fc['calendar'].columns)
            for arm in ['calendar', 'day5', 'pooled_day5', 'hybrid']:
                x = base.copy(); x[cal] = fc[arm].iloc[:, :13].to_numpy(); x = pd.concat([x, fc[arm].iloc[:, 13:]], axis=1)
                frames[name, arm] = x
        def pick(sel, m):
            c = sel[sel.state.eq(state) & sel.year.eq(year) & sel.horizon.eq(1) & sel['mode'].eq('rich_calendar') & sel.model.eq(m)]
            assert len(c) == 1
            return json.loads(c.parameters.iloc[0])
        pr, pt = pick(sel_r, 'ridge'), pick(sel_t, 'lightgbm')
        for month, seg in group.groupby(group.origin.dt.to_period('M')):
            refit = pd.Timestamp(month.start_time); cutoff = refit-pd.Timedelta(days=1)
            q_index = pd.DatetimeIndex(seg.origin)
            for cfg in configs():
                m = cfg['model']
                if m == 'ridge':
                    kind, params = 'ridge', pr
                elif m.startswith('ridge_alpha'):
                    kind, params = 'ridge', {'alpha': float(m[len('ridge_alpha'):])}
                elif m == 'lgbm_leaf2':
                    kind, params = 'lightgbm', dict(pt, min_child_samples=2)
                else:
                    kind, params = 'lightgbm', pt
                for arm in cfg['arms']:
                    x = frames[cfg['ledger'], arm]
                    if kind == 'lightgbm':
                        x = x.astype(np.float32)
                    xx, yy, log = fitting_cases(x, observed, 1, cutoff, context=cfg['W'])
                    assert pd.Timestamp(log['training_target_max']) < refit <= seg.origin.min()
                    assert cutoff-pd.Timedelta(days=cfg['W']-1) >= pd.Timestamp('2015-01-01'), 'window must lie inside the ledger years'
                    mod = make_model(kind, params, FIXED).fit(xx, yy)
                    s = seg.copy(); s['prediction'] = mod.predict(x.reindex(q_index).to_numpy())
                    s['mase_scale'] = engine.scale(data, state, int(year))
                    s['W'] = cfg['W']; s['model'] = m; s['arm'] = arm; s['ledger'] = cfg['ledger']; rows.append(s)
                    fits.append(dict(state=state, year=int(year), refit=str(refit.date()), W=cfg['W'], model=m, arm=arm,
                                     ledger=cfg['ledger'], training_n=log['training_n']))
        print(TEST, EXP, state, year, flush=True)
    d = pd.concat(rows, ignore_index=True)
    d.to_csv(OUT/'predictions.csv', index=False)
    pd.DataFrame(fits).to_csv(OUT/'fits.csv', index=False)
    dump(OUT/'run.json', dict(completed_utc=datetime.now(timezone.utc).isoformat(), rows=len(d), predictions_sha256=sha(OUT/'predictions.csv')))


if __name__ == '__main__':
    main()
