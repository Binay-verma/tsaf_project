"""Execute the frozen festival-identity intervention and its negative controls."""
from pathlib import Path
import argparse
from datetime import datetime, timezone
import hashlib
import json
import time
import traceback
import numpy as np
import pandas as pd
from forecasting import ROOT, load_data, causal_fill
from festival_feature_design import OUT, BASE, ARMS, EXTRA, KEY, frames, sha, dump


def setup(worker, primary=False):
    p = json.loads((OUT/'protocol.json').read_text())
    for f, h in p['input_hashes'].items():
        assert sha(ROOT/f) == h, f
    for f, h in p['design_hashes'].items():
        assert sha(OUT/f) == h, f
    out = OUT/worker
    out.mkdir(exist_ok=True)
    if any((out/f).exists() for f in ['started.json', 'predictions.csv', 'checkpoint.csv']):
        raise FileExistsError('Preserve interrupted/completed worker; version a new run')
    dump(out/'started.json', dict(worker=worker, started_utc=datetime.now(timezone.utc).isoformat()))
    cases = pd.read_csv(OUT/('primary_cases.csv' if primary else 'window_cases.csv'), parse_dates=['origin', 'date'])
    data = load_data('latest')
    cases['actual'] = [data.loc[r.date, r.state] for r in cases.itertuples(index=False)]
    assert cases.actual.notna().all() and (cases.actual > 0).all()
    return p, out, cases, data


def scale(data, state, year):
    end = pd.Timestamp(f'{year-1}-12-31')
    y = data[state].loc[end-pd.Timedelta(days=729):end]
    return float((y-y.shift(7)).abs().mean())


def ledger_bound(dates):
    assert pd.Timestamp(min(dates)) >= pd.Timestamp('2022-01-01')
    assert pd.Timestamp(max(dates)) <= pd.Timestamp('2025-12-31')


def input_pair(observed, frame, origin):
    target = causal_fill(observed).loc[:origin-pd.Timedelta(days=1)].tail(730).to_numpy(dtype=np.float32)
    dates = pd.date_range(origin-pd.Timedelta(days=730), periods=744)
    ledger_bound(dates)
    cov = frame.reindex(dates).to_numpy(dtype=np.float32).T
    assert target.shape == (730,) and cov.shape[1] == 744
    assert np.isfinite(target).all() and np.isfinite(cov).all()
    return target, cov


def regression(worker):
    from robust_baselines import design_frame, fitting_cases, make_model
    p, out, cases, data = setup(worker)
    model_name = 'ridge' if worker == 'ridge' else 'lightgbm'
    old = 'strong_refit_v1' if model_name == 'ridge' else 'stable_tree_refit_v2'
    selected = pd.read_csv(ROOT/f'results/{old}/selected.csv')
    fixed = json.loads((ROOT/f'results/{old}/protocol.json').read_text())
    arms = ARMS if worker == 'lightgbm_capacity2' else ARMS+EXTRA
    rows, fits, selections, checks = [], [], [], []
    started = time.perf_counter()
    try:
        for (state, year, horizon), group in cases.groupby(['state', 'year', 'horizon']):
            observed = data[state]
            fc = frames(data.index, state)
            base, _ = design_frame(observed, state, int(horizon), 'rich_calendar')
            chosen = selected[selected.state.eq(state) & selected.year.eq(year) & selected.horizon.eq(horizon) & selected['mode'].eq('rich_calendar') & selected.model.eq(model_name)]
            assert len(chosen) == 1
            params = json.loads(chosen.parameters.iloc[0])
            if worker == 'lightgbm_capacity2':
                params['min_child_samples'] = 2
            selections.append(dict(state=state, year=int(year), horizon=int(horizon),
                original_configuration=int(chosen.configuration.iloc[0]), parameters=params,
                policy='Same original pre-year rich-calendar parameters for every arm; capacity2 override prespecified' if worker == 'lightgbm_capacity2' else 'Same original pre-year rich-calendar parameters for every arm'))
            for arm in arms:
                additional = fc[arm].iloc[:, 13:]
                extra = additional.reindex(data.index+pd.Timedelta(days=int(horizon)-1)).copy()
                extra.index = data.index
                x = pd.concat([base, extra], axis=1)
                if model_name == 'lightgbm':
                    x = x.astype(np.float32)
                chunks = []
                for month, segment in group.groupby(group.origin.dt.to_period('M')):
                    refit = pd.Timestamp(month.start_time)
                    cutoff = refit-pd.Timedelta(days=1)
                    training_first_target = cutoff-pd.Timedelta(days=729)+pd.Timedelta(days=int(horizon)-1)
                    ledger_bound([training_first_target, cutoff, segment.date.min(), segment.date.max()])
                    xx, yy, log = fitting_cases(x, observed, int(horizon), cutoff)
                    assert pd.Timestamp(log['training_target_max']) < refit <= segment.origin.min()
                    oo = pd.DatetimeIndex(segment.origin)
                    query = x.reindex(oo).to_numpy()
                    tick = time.perf_counter()
                    model = make_model(model_name, params, fixed).fit(xx, yy)
                    predicted = model.predict(query)
                    a = segment.copy()
                    a['prediction'] = predicted
                    a['mase_scale'] = scale(data, state, int(year))
                    a['model'] = worker
                    a['arm'] = arm
                    chunks.append(a)
                    # Archive parameters and actual matrices, not an unsupported
                    # assertion that all rare indicators are learnable.
                    support = {} if not additional.shape[1] else dict(zip(additional.columns,
                        np.count_nonzero(xx[:, -additional.shape[1]:], axis=0).astype(int).tolist()))
                    fits.append(dict(model=worker, arm=arm, state=state, year=int(year), horizon=int(horizon),
                        refit=str(refit.date()), parameters=params, feature_count=xx.shape[1],
                        training_target_min_bound=str(training_first_target.date()),
                        training_X_sha256=hashlib.sha256(xx.tobytes()).hexdigest(),
                        training_y_sha256=hashlib.sha256(yy.tobytes()).hexdigest(),
                        query_X_sha256=hashlib.sha256(query.tobytes()).hexdigest(),
                        feature_nonzero_training_counts=support, seconds=time.perf_counter()-tick, **log))
                arm_rows = pd.concat(chunks, ignore_index=True)
                rows.append(arm_rows)
                pd.concat(rows, ignore_index=True).to_csv(out/'checkpoint.csv', index=False)
                dump(out/'fit_log.json', fits)
                if arm == 'calendar' and worker != 'lightgbm_capacity2':
                    old_predictions = pd.read_csv(ROOT/'results/multifestival_models_v1/predictions.csv', parse_dates=['origin', 'date'])
                    config = 'ridge_rich_calendar_monthly' if worker == 'ridge' else 'lightgbm_stable_calendar_monthly'
                    old_predictions = old_predictions[old_predictions.configuration.eq(config)]
                    comparison = arm_rows.merge(old_predictions[KEY+['prediction']], on=KEY, suffixes=('_new', '_old'), validate='one_to_one')
                    assert len(comparison) == len(group)
                    np.testing.assert_allclose(comparison.prediction_new, comparison.prediction_old, rtol=1e-9, atol=1e-7)
                    checks.append(dict(state=state, year=int(year), horizon=int(horizon),
                        baseline_old_prediction_maxdiff=float(abs(comparison.prediction_new-comparison.prediction_old).max())))
            print(worker, state, year, horizon, 'complete', flush=True)
        d = pd.concat(rows, ignore_index=True)
        assert len(d) == len(cases)*len(arms) and np.isfinite(d.prediction).all()
        d.to_csv(out/'predictions.csv', index=False)
        dump(out/'selection_reuse.json', selections)
        dump(out/'baseline_reproduction.json', checks)
        dump(out/'run.json', dict(model=worker, completed_utc=datetime.now(timezone.utc).isoformat(),
            fits=len(fits), rows=len(d), cases_per_arm=len(cases), arms=arms, seconds=time.perf_counter()-started,
            predictions_sha256=sha(out/'predictions.csv'), protocol_sha256=sha(OUT/'protocol.json')))
    except Exception:
        (out/'failure.txt').write_text(traceback.format_exc())
        dump(out/'fit_log.json', fits)
        raise


def sarimax():
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    from multifestival_models import fit_checked
    p, out, cases, data = setup('sarimax')
    rows, fits, deployments = [], [], []
    started = time.perf_counter()
    try:
        for (state, year), group in cases.groupby(['state', 'year']):
            y = causal_fill(data[state])/100.
            fc = frames(data.index, state)
            end = pd.Timestamp(f'{year-1}-12-31')
            tr = y.loc[end-pd.Timedelta(days=729):end]
            ledger_bound(tr.index)
            origins = sorted(group.origin.unique())
            for arm in ARMS:
                cal = fc[arm]
                fit = fit_checked(SARIMAX(tr, exog=cal.reindex(tr.index), order=(1, 0, 0),
                    seasonal_order=(1, 0, 0, 7), trend='n', enforce_stationarity=False),
                    'sarimax', fits, dict(configuration=arm, state=state, year=int(year),
                        training_end=str(end.date()), missing_past_filled=int(data[state].reindex(tr.index).isna().sum())))
                params = {str(k): float(v) for k, v in zip(fit.param_names, fit.params)}
                cutoff = end+pd.Timedelta(days=1)
                for origin in origins:
                    origin = pd.Timestamp(origin)
                    updated = y.loc[cutoff:origin-pd.Timedelta(days=1)]
                    if len(updated):
                        fit = fit.extend(updated, exog=cal.reindex(updated.index))
                    assert fit.model.data.row_labels.max() < origin
                    dates = pd.date_range(origin, periods=14)
                    ledger_bound(dates)
                    predicted = np.asarray(fit.forecast(14, exog=cal.reindex(dates)))*100.
                    segment = group[group.origin.eq(origin)].copy()
                    segment['prediction'] = [predicted[h-1] for h in segment.horizon]
                    segment['mase_scale'] = scale(data, state, int(year))
                    segment['model'] = 'sarimax'; segment['arm'] = arm
                    rows.append(segment)
                    deployments.append(dict(arm=arm, state=state, origin=str(origin.date()),
                        fitting_target_max=str(end.date()), context_max=str((origin-pd.Timedelta(days=1)).date()),
                        parameters=params))
                    cutoff = origin
                pd.concat(rows, ignore_index=True).to_csv(out/'checkpoint.csv', index=False)
                dump(out/'fit_attempts.json', fits)
                dump(out/'deployments.json', deployments)
                print('sarimax', state, year, arm, 'complete', flush=True)
        d = pd.concat(rows, ignore_index=True)
        assert len(d) == len(cases)*len(ARMS) and np.isfinite(d.prediction).all()
        d.to_csv(out/'predictions.csv', index=False)
        dump(out/'run.json', dict(model='sarimax', completed_utc=datetime.now(timezone.utc).isoformat(),
            fit_attempts=len(fits), rows=len(d), cases_per_arm=len(cases), arms=ARMS,
            seconds=time.perf_counter()-started, predictions_sha256=sha(out/'predictions.csv'), protocol_sha256=sha(OUT/'protocol.json')))
    except Exception:
        (out/'failure.txt').write_text(traceback.format_exc())
        dump(out/'fit_attempts.json', fits)
        dump(out/'deployments.json', deployments)
        raise


def foundation(worker):
    import torch
    p, out, cases, data = setup(worker, primary=True)
    torch.set_num_threads(p['threads']); torch.manual_seed(p['seed']); np.random.seed(p['seed'])
    if worker == 'chronos':
        from chronos import Chronos2Pipeline
        identity = json.loads((ROOT/'results/mechanism_controls_v1/chronos_download.json').read_text())
        for f in identity['files']:
            assert sha(f['path']) == f['sha256']
        weight = next(f for f in identity['files'] if f['name'] == 'model.safetensors')
        model = Chronos2Pipeline.from_pretrained(str(Path(weight['path']).parent), device_map='cpu', local_files_only=True)
        levels = list(model.quantiles); weight_sha = weight['sha256']
    else:
        from timesfm3 import TimesFM3Evaluator, ModelConfig
        identity = json.loads((ROOT/'results/second_model_audit_v1/weight_download.json').read_text())
        assert sha(identity['path']) == identity['sha256']
        model = TimesFM3Evaluator(ModelConfig(checkpoint_path=str(Path(identity['path']).parent), device='cpu',
            per_core_batch_size=p['batch'], local_files_only=True))
        levels = [q/10 for q in range(1, 10)]; weight_sha = identity['sha256']
    all_frames = {s: frames(data.index, s) for s in data}
    tasks = cases[['state', 'year', 'origin']].drop_duplicates().sort_values(['state', 'origin'])
    assert len(tasks) == 72
    rows, inputs_log, batches, solo_audit = [], [], [], []
    started = time.perf_counter()

    def predict(inputs, names):
        if worker == 'chronos':
            packed = [dict(target=target, past_covariates={name: cov[i, :730] for i, name in enumerate(names)},
                future_covariates={name: cov[i, 730:] for i, name in enumerate(names)}) for target, cov in inputs]
            output = model.predict(packed, prediction_length=14, batch_size=128, context_length=730, cross_learning=False)
            qq = [q[0].detach().cpu().numpy().T for q in output]
            return [(q[:, levels.index(.5)], q) for q in qq]
        output = list(model.predict_batch([x[0] for x in inputs], horizon=14,
            past_future_covariates=[x[1] for x in inputs], return_quantiles=True, use_symmetric_averaging=False))
        return [(np.asarray(x.forecast).squeeze(), np.asarray(x.quantiles).squeeze()) for x in output]

    try:
        for arm in ARMS:
            for offset in range(0, len(tasks), p['batch']):
                group = list(tasks.iloc[offset:offset+p['batch']].itertuples(index=False))
                inputs = [input_pair(data[t.state], all_frames[t.state][arm], t.origin) for t in group]
                names = list(all_frames[group[0].state][arm])
                assert all(names == list(all_frames[t.state][arm]) for t in group)
                for task, (target, cov) in zip(group, inputs):
                    changed = data[task.state].copy(); changed.loc[task.origin:] = 1e12
                    tt, cc = input_pair(changed, all_frames[task.state][arm], task.origin)
                    np.testing.assert_array_equal(target, tt); np.testing.assert_array_equal(cov, cc)
                    inputs_log.append(dict(arm=arm, state=task.state, origin=str(task.origin.date()),
                        target_sha256=hashlib.sha256(target.tobytes()).hexdigest(), covariate_sha256=hashlib.sha256(cov.tobytes()).hexdigest(),
                        feature_count=cov.shape[0], context_start=str((task.origin-pd.Timedelta(days=730)).date()),
                        context_end=str((task.origin-pd.Timedelta(days=1)).date()), future_target_perturbation_invariant=True,
                        past_nonzero_counts=np.count_nonzero(cov[13:, :730], axis=1).astype(int).tolist()))
                tick = time.perf_counter()
                output = predict(inputs, names)
                assert len(output) == len(group)
                if offset == 0:
                    for pair, batch_result in zip(inputs, output):
                        solo = predict([pair], names)[0]
                        np.testing.assert_allclose(solo[0], batch_result[0], rtol=2e-4, atol=1e-3)
                        solo_audit.append(dict(arm=arm, max_abs_difference=float(abs(solo[0]-batch_result[0]).max())))
                    dump(out/'solo_batch_audit.json', solo_audit)
                for task, (point, quantiles) in zip(group, output):
                    assert point.shape == (14,) and quantiles.shape == (14, len(levels))
                    assert np.isfinite(point).all() and np.isfinite(quantiles).all()
                    selected = cases[cases.state.eq(task.state) & cases.origin.eq(task.origin)]
                    for r in selected.itertuples(index=False):
                        j = r.horizon-1
                        rows.append(dict(family=r.family, state=r.state, year=r.year, origin=str(r.origin.date()),
                            date=str(r.date.date()), horizon=r.horizon, prediction=float(point[j]), actual=float(r.actual),
                            mase_scale=scale(data, r.state, int(r.year)), model=worker, arm=arm,
                            **{f'q_{int(round(level*1000)):03d}': float(v) for level, v in zip(levels, quantiles[j])}))
                batches.append(dict(arm=arm, offset=offset, tasks=len(group), seconds=time.perf_counter()-tick))
                pd.DataFrame(rows).to_csv(out/'checkpoint.csv', index=False)
                dump(out/'batches.json', batches); dump(out/'inputs.json', inputs_log)
                print(worker, arm, offset+len(group), '/', len(tasks), flush=True)
        d = pd.DataFrame(rows)
        assert len(d) == len(cases)*len(ARMS)
        d.to_csv(out/'predictions.csv', index=False)
        qcols = [f'q_{int(round(q*1000)):03d}' for q in levels]
        dump(out/'run.json', dict(model=worker, completed_utc=datetime.now(timezone.utc).isoformat(),
            rows=len(d), cases_per_arm=len(cases), arms=ARMS, inference_tasks=len(tasks)*len(ARMS),
            seconds=time.perf_counter()-started, weight_sha256=weight_sha,
            native_quantile_crossings=int((np.diff(d[qcols].to_numpy(), axis=1)<0).sum()),
            predictions_sha256=sha(out/'predictions.csv'), protocol_sha256=sha(OUT/'protocol.json')))
    except Exception:
        (out/'failure.txt').write_text(traceback.format_exc())
        dump(out/'inputs.json', inputs_log)
        raise


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('worker', choices=['ridge', 'lightgbm', 'lightgbm_capacity2', 'sarimax', 'chronos', 'timesfm'])
    w = p.parse_args().worker
    if w in ['chronos', 'timesfm']:
        foundation(w)
    elif w == 'sarimax':
        sarimax()
    else:
        regression(w)
