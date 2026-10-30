"""Versioned exploratory rich baselines and genuinely past-only refits."""
from pathlib import Path
import argparse
import hashlib
import importlib.metadata
import json
import time
import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from forecasting import ROOT, STATES, load_data, causal_fill
from extended_validation import features


def rich_history(observed, horizon):
    y = causal_fill(observed)
    x = pd.DataFrame({f'lag_{k}': y.shift(k) for k in
                      [1, 2, 3, 7, 14, 21, 28, 56, 364, 365, 366]})
    for w in [7, 28, 56]:
        roll = y.shift(1).rolling(w)
        for name in ['mean', 'std', 'min', 'max']:
            x[f'{name}_{w}'] = getattr(roll, name)()
    x['trend_7_28'] = x.mean_7-x.mean_28
    for lag in [364, 365, 366]:
        assert lag-horizon+1 > 0
        x[f'target_annual_{lag}'] = y.shift(lag-horizon+1)
    return x


def design_frame(observed, state, horizon, mode):
    x = rich_history(observed, horizon)
    cal, cols, event = features(observed.index, state)
    if mode != 'rich_history':
        names = cols['D_regional_festival' if mode == 'rich_regional' else 'B_calendar']
        # Reindex covariates at target dates, but retain origin row index.
        c = cal.reindex(observed.index+pd.Timedelta(days=horizon-1))[names].copy()
        c.index = observed.index
        x = pd.concat([x, c], axis=1)
    return x, event


def fitting_cases(frame, observed, horizon, cutoff, context=730):
    cutoff = pd.Timestamp(cutoff)
    origins = pd.date_range(cutoff-pd.Timedelta(days=context-1),
                            cutoff-pd.Timedelta(days=horizon-1))
    dates = origins+pd.Timedelta(days=horizon-1)
    x = frame.reindex(origins).to_numpy()
    y = observed.reindex(dates).to_numpy()
    valid = np.isfinite(x).all(axis=1) & np.isfinite(y)
    if valid.sum() < 365:
        raise ValueError('Fewer than 365 usable fitting labels')
    assert dates[valid].max() <= cutoff
    return x[valid], y[valid], dict(training_n=int(valid.sum()),
        training_target_max=str(dates[valid].max().date()),
        training_origin_max=str(origins[valid].max().date()))


def make_model(model, parameters, protocol):
    if model == 'ridge':
        return make_pipeline(StandardScaler(), Ridge(**parameters))
    return LGBMRegressor(**parameters, **protocol['lightgbm_fixed'])


def evaluation_origins(year, index):
    end = min(pd.Timestamp(f'{year}-12-18'), index.max()-pd.Timedelta(days=13))
    return pd.date_range(f'{year}-01-01', end)


def score_predictions(d, out, identity):
    assert not d.duplicated(identity+['state', 'origin', 'horizon']).any()
    assert np.isfinite(d.prediction).all()
    assert ((pd.to_datetime(d.date)-pd.to_datetime(d.origin)).dt.days == d.horizon-1).all()
    source = load_data('latest')
    for state, g in d.groupby('state'):
        np.testing.assert_allclose(g.actual, source[state].reindex(pd.to_datetime(g.date)), equal_nan=True)
    d = d[d.actual.notna()].copy()
    d['ae'] = abs(d.actual-d.prediction)
    d['scaled'] = d.ae/d.mase_scale
    sets = [set(map(tuple, g[['state', 'origin', 'horizon']].to_numpy()))
            for _, g in d.groupby(identity)]
    assert all(s == sets[0] for s in sets)
    metrics = []
    for scope, mask in [('all', np.ones(len(d), bool)), ('event', d.event.eq(1)),
                        ('non_event', d.event.eq(0))]:
        a = d[mask].groupby(identity+['state', 'year', 'horizon']).agg(
            MASE=('scaled', 'mean'), MAE_GWh=('ae', 'mean'), n=('ae', 'size')).reset_index()
        a['scope'] = scope
        metrics.append(a)
    m = pd.concat(metrics, ignore_index=True)
    m.to_csv(out/'metrics_state_year.csv', index=False)
    macro = m.groupby(identity+['year', 'horizon', 'scope']).MASE.mean().reset_index()
    macro.to_csv(out/'metrics_macro.csv', index=False)
    return {'scored_rows': len(d), 'cases_per_configuration': len(sets[0]),
            'checks': ['finite/unique predictions', 'matched cases', 'source labels', 'lead/date alignment']}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, default=ROOT/'results/strong_refit_v1')
    args = parser.parse_args()
    out = args.out
    p = json.loads((out/'protocol.json').read_text())
    if (out/'predictions.csv').exists() or (out/'fit_log.csv').exists():
        raise FileExistsError('Preserve completed/interrupted runs; use a new directory')
    start = time.perf_counter()
    source = load_data('latest')
    rows, selection, chosen, fits, failures = [], [], [], [], []
    try:
        for state in STATES:
            observed = source[state]
            for year in p['years']:
                cutoff = pd.Timestamp(f'{year-1}-12-31')
                origins = evaluation_origins(year, source.index)
                tr = observed.loc[cutoff-pd.Timedelta(days=729):cutoff]
                scale = float((tr-tr.shift(7)).abs().mean())
                for h in p['leads']:
                    dates = origins+pd.Timedelta(days=h-1)
                    for mode in p['modes']:
                        frame, event = design_frame(observed, state, h, mode)
                        vs = cutoff-pd.Timedelta(days=179)
                        x, y, training_log = fitting_cases(frame, observed, h, vs-pd.Timedelta(days=1))
                        vo = pd.date_range(vs, cutoff-pd.Timedelta(days=h-1))
                        vd = vo+pd.Timedelta(days=h-1)
                        vx, vy = frame.reindex(vo).to_numpy(), observed.reindex(vd).to_numpy()
                        valid = np.isfinite(vx).all(axis=1) & np.isfinite(vy)
                        assert pd.Timestamp(training_log['training_target_max']) < vs
                        for name in p['models']:
                            grid = ([dict(alpha=a) for a in p['ridge_alphas']] if name == 'ridge'
                                    else p['lightgbm_grid'])
                            key = dict(state=state, year=year, horizon=h, mode=mode, model=name)
                            scores = []
                            for i, params in enumerate(grid):
                                try:
                                    model = make_model(name, params, p).fit(x, y)
                                    loss = float(np.mean(abs(vy[valid]-model.predict(vx[valid]))))
                                    selection.append(dict(**key, configuration=i, MAE=loss,
                                        status='ok', parameters=json.dumps(params), **training_log,
                                        validation_origin_min=str(vs.date()),
                                        validation_target_max=str(vd[valid].max().date())))
                                    scores.append((loss, i, params))
                                except Exception as exc:
                                    failure = dict(**key, configuration=i, error=repr(exc))
                                    failures.append(failure)
                                    selection.append(dict(**key, configuration=i, MAE=np.nan, status='failed'))
                            if not scores:
                                raise RuntimeError('Every validation fit failed')
                            loss, i, params = min(scores, key=lambda a: (a[0], a[1]))
                            chosen.append(dict(**key, configuration=i, MAE=loss, parameters=json.dumps(params)))
                            for schedule in p['refits']:
                                partitions = [(pd.Timestamp(f'{year}-01-01'), origins)]
                                if schedule == 'monthly':
                                    partitions = [(o.iloc[0].replace(day=1), o) for _, o in
                                                  pd.Series(origins, index=origins).groupby(origins.month)]
                                    partitions = [(pd.Timestamp(ref), pd.DatetimeIndex(o)) for ref, o in partitions]
                                pred = pd.Series(index=origins, dtype=float)
                                for refit, oo in partitions:
                                    xx, yy, log = fitting_cases(frame, observed, h, refit-pd.Timedelta(days=1))
                                    assert pd.Timestamp(log['training_target_max']) < refit <= oo.min()
                                    tick = time.perf_counter()
                                    model = make_model(name, params, p).fit(xx, yy)
                                    pred.loc[oo] = model.predict(frame.reindex(oo).to_numpy())
                                    fits.append(dict(**key, schedule=schedule, refit=str(refit.date()),
                                        configuration=i, seconds=time.perf_counter()-tick, **log))
                                rows.append(pd.DataFrame(dict(**key, schedule=schedule, origin=origins,
                                    date=dates, prediction=pred.to_numpy(), actual=observed.reindex(dates).to_numpy(),
                                    event=event.reindex(dates).astype(int).to_numpy(), mase_scale=scale)))
                pd.concat(rows).to_csv(out/'checkpoint_predictions.csv', index=False)
                pd.DataFrame(selection).to_csv(out/'selection.csv', index=False)
                pd.DataFrame(chosen).to_csv(out/'selected.csv', index=False)
                pd.DataFrame(fits).to_csv(out/'fit_log.csv', index=False)
                print('Completed rich refits', state, year, flush=True)
        d = pd.concat(rows, ignore_index=True)
        d.to_csv(out/'predictions.csv', index=False)
        checks = score_predictions(d, out, ['model', 'mode', 'schedule'])
        protected = json.loads((out/'protected_before.json').read_text())
        assert all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest() == h for n, h in protected.items())
        info = dict(seconds=time.perf_counter()-start, rows=len(d), selection_fits=len(selection),
            deployment_fits=len(fits), selected=len(chosen), failures=failures, checks=checks,
            packages={n: importlib.metadata.version(n) for n in ['numpy', 'pandas', 'scikit-learn', 'lightgbm']},
            hashes={str(f.relative_to(ROOT)): hashlib.sha256(f.read_bytes()).hexdigest() for f in
                    [Path(__file__), ROOT/'src/forecasting.py', ROOT/'src/extended_validation.py',
                     out/'protocol.json', ROOT/'data/external/latest_state_energy_GWh.csv']})
        (out/'run.json').write_text(json.dumps(info, indent=2)+'\n')
        print(json.dumps(info, indent=2), flush=True)
    finally:
        (out/'failures.json').write_text(json.dumps(failures, indent=2)+'\n')


if __name__ == '__main__':
    main()
