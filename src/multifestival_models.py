"""Fixed missing-model comparisons on the frozen multi-festival cases."""
from pathlib import Path
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import time
import traceback
import warnings
import numpy as np
import pandas as pd
from forecasting import ROOT, load_data, causal_fill
from multifestival_cached import KEY, sha, dump, metrics
from timesfm_fixture import build_input

BASE = ROOT/'results/multifestival_cached_v1'
OUT = ROOT/'results/multifestival_models_v1'
NEW_CONFIGS = ['sarimax_history_annual', 'sarimax_calendar_annual',
    'ets_weekly_monthly', 'chronos_calendar', 'timesfm_history', 'timesfm_calendar']


def prepare():
    if OUT.exists():
        raise FileExistsError('Version a new experiment')
    OUT.mkdir(parents=True)
    for f in ['expected_cases.csv', 'excluded_labels.csv']:
        (OUT/f).write_bytes((BASE/f).read_bytes())
    files = ['src/multifestival_models.py', 'src/multifestival_cached.py', 'src/timesfm_fixture.py',
        'src/extended_validation.py', 'src/forecasting.py',
        'data/external/latest_state_energy_GWh.csv',
        'results/multifestival_cached_v1/protocol.json', 'results/multifestival_cached_v1/predictions.csv',
        'results/mechanism_controls_v1/chronos_download.json',
        'results/second_model_audit_v1/weight_download.json']
    p = dict(experiment=OUT.name, created_utc=datetime.now(timezone.utc).isoformat(),
        status='Exploratory extension recorded after cached diagnostic outcomes; model families/arms already proposed before those diagnostics. No clean-test model selection.',
        cases='Identical528eligible cases and fixed five-family windows from multifestival_cached_v1; no case intersection selected by forecast success',
        cases_sha256=sha(OUT/'expected_cases.csv'), new_configurations=NEW_CONFIGS,
        cached_configurations='All9configurations retained unchanged; scores combined only on exact same cases',
        leads=[1, 7, 14], horizon=14, context=730, seed=42, batch=4, threads=2,
        ordinary_calendar='Same13weekday/Fourier channels as existing studies; no new event covariates. Chronos uses native future covariates with cross_learning=False; TimesFM symmetric averaging=False.',
        sarimax=dict(order=[1, 0, 0], seasonal_order=[1, 0, 0, 7],
            fitting='Annual730-day pre-year fit; history uses constant trend, calendar uses13exogenous channels and no constant. Fixed parameters; extend state only through origin-1. Target units divided by100 for numerical fitting and multiplied back.',
            retries='L-BFGS150 then500iterations, then Powell500 only if nonconverged. Training objective/convergence only, no evaluation-based choices; retain every attempt/warning.'),
        ets=dict(model='statsmodels ETSModel', error='add', trend=None, seasonal='add', seasonal_periods=7,
            initialization_method='estimated',
            fitting='Refit at first calendar day of each origin month using preceding730days; fixed specification, no hyperparameter search. Between refits smooth same fitted parameters/initial states through origin-1 without optimisation.',
            retries='200 then500iterations only if nonconverged; retain every attempt. Additive model has no positivity requirement/clipping.'),
        past_missing='Causal weekly/last-value fill only in past contexts and classical training series; record missing training counts. Score positive recorded labels only. Source publication availability remains retrospective.',
        foundation_identity='Reuse individually audited pinned local weights/code, verify actual hashes before inference. No fine-tuning, no network/latest checkpoint. Preserve native quantiles; no sorting/clipping.',
        metrics='Same prior-year730-calendar-day weekly-difference scale, equal state/year/festival weighting as cached protocol. All arms/failures and per-state/year metrics retained.',
        inference_checks='Future-target perturbation invariance for every task; first batch solo-vs-batch per model/mode; finite forecasts and native quantile order diagnostics. Input target/covariate hashes saved.',
        failure_policy='Keep checkpoints and traceback; do not silently omit failed configs/cases or shrink comparison. New directory for altered model choices; no overwriting old runs.',
        limits=['Historical pretraining/proxy overlap', 'Two years, dependent states/days and overlapping holidays',
            'Unequal local refit/feature/validation budgets; deployment-policy comparison', 'No causal, universal winner, new-method or final-test claim',
            'No changes to source/frozen prospective predictions; no future outcomes retrieved'],
        input_hashes={f: sha(ROOT/f) for f in files},
        packages={x: importlib.metadata.version(x) for x in ['numpy', 'pandas', 'statsmodels', 'torch', 'timesfm', 'chronos-forecasting', 'transformers']})
    dump(OUT/'protocol.json', p)
    print('PREPARED6new configurations on528fixed cases')


def setup(worker):
    p = json.loads((OUT/'protocol.json').read_text())
    for f, h in p['input_hashes'].items():
        assert sha(ROOT/f) == h, f
    assert sha(OUT/'expected_cases.csv') == p['cases_sha256']
    out = OUT/worker
    out.mkdir(exist_ok=True)
    if (out/'predictions.csv').exists() or (out/'checkpoint.csv').exists() or (out/'started.json').exists():
        raise FileExistsError('Preserve completed/interrupted worker; do not overwrite')
    dump(out/'started.json', dict(started_utc=datetime.now(timezone.utc).isoformat(), worker=worker))
    cases = pd.read_csv(OUT/'expected_cases.csv', parse_dates=['origin', 'date'])
    excluded = pd.read_csv(OUT/'excluded_labels.csv', parse_dates=['origin', 'date'])
    if len(excluded):
        cases = cases.merge(excluded[KEY].drop_duplicates().assign(exclude=True), on=KEY, how='left')
        cases = cases[cases.exclude.isna()].drop(columns='exclude')
    return p, out, cases, load_data('latest')


def scale_for(data, state, year):
    end = pd.Timestamp(f'{year-1}-12-31')
    tr = data[state].loc[end-pd.Timedelta(days=729):end]
    return float((tr-tr.shift(7)).abs().mean())


def pack_rows(rows, group, predicted, config, scale):
    for r in group.itertuples(index=False):
        rows.append(dict(family=r.family, state=r.state, year=r.year, origin=str(r.origin.date()),
            date=str(r.date.date()), horizon=r.horizon, prediction=float(predicted[r.horizon-1]),
            actual=r.actual, mase_scale=scale, configuration=config))


def fit_checked(model, family, log, identity):
    attempts = [('lbfgs', 150), ('lbfgs', 500), ('powell', 500)] if family == 'sarimax' else [('lbfgs', 200), ('lbfgs', 500)]
    result = None
    for method, n in attempts:
        tick = time.perf_counter()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            kw = dict(maxiter=n, disp=False)
            if family == 'sarimax':
                kw['method'] = method
            if result is not None:
                kw['start_params'] = result.params
            result = model.fit(**kw)
        converged = bool(result.mle_retvals.get('converged', False))
        log.append(dict(**identity, optimizer=method, maxiter=n, converged=converged,
            training_loglikelihood=float(result.llf), seconds=time.perf_counter()-tick,
            warnings=[str(w.message) for w in caught]))
        if converged:
            return result
    raise RuntimeError(f'Nonconverged {family}: {identity}; all attempts retained')


def classical():
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    from statsmodels.tsa.exponential_smoothing.ets import ETSModel
    from extended_validation import features
    p, out, cases, data = setup('classical')
    cases['actual'] = [data.loc[r.date, r.state] for r in cases.itertuples(index=False)]
    rows, fits, deployments = [], [], []
    started = time.perf_counter()
    try:
        for (state, year), group in cases.groupby(['state', 'year']):
            y = causal_fill(data[state])/100.
            cal, names, _ = features(data.index, state)
            origins = sorted(group.origin.unique())
            end = pd.Timestamp(f'{year-1}-12-31')
            tr = y.loc[end-pd.Timedelta(days=729):end]
            scale = scale_for(data, state, year)
            for mode in ['history', 'calendar']:
                config = f'sarimax_{mode}_annual'
                cols = names['B_calendar'] if mode == 'calendar' else []
                model = SARIMAX(tr, exog=cal.loc[tr.index, cols] if cols else None,
                    order=(1, 0, 0), seasonal_order=(1, 0, 0, 7), trend='n' if cols else 'c', enforce_stationarity=False)
                fit = fit_checked(model, 'sarimax', fits, dict(configuration=config, state=state, year=int(year),
                    training_end=str(end.date()), missing_past_filled=int(data[state].reindex(tr.index).isna().sum())))
                cutoff = end+pd.Timedelta(days=1)
                for origin in origins:
                    origin = pd.Timestamp(origin)
                    upd = y.loc[cutoff:origin-pd.Timedelta(days=1)]
                    if len(upd):
                        fit = fit.extend(upd, exog=cal.loc[upd.index, cols] if cols else None)
                    assert fit.model.data.row_labels.max() < origin
                    dates = pd.date_range(origin, periods=14)
                    predicted = np.asarray(fit.forecast(14, exog=cal.loc[dates, cols] if cols else None))*100.
                    pack_rows(rows, group[group.origin.eq(origin)], predicted, config, scale)
                    deployments.append(dict(configuration=config, state=state, origin=str(origin.date()),
                        fitting_target_max=str(end.date()), context_target_max=str((origin-pd.Timedelta(days=1)).date())))
                    cutoff = origin
                pd.DataFrame(rows).to_csv(out/'checkpoint.csv', index=False)
                dump(out/'fit_attempts.json', fits)
                print(config, state, year, 'completed', flush=True)
            fit, month, training_start = None, None, None
            for origin in origins:
                origin = pd.Timestamp(origin)
                boundary = origin.replace(day=1)
                if boundary != month:
                    month = boundary
                    end = month-pd.Timedelta(days=1)
                    training_start = end-pd.Timedelta(days=729)
                    tr = y.loc[training_start:end]
                    model = ETSModel(tr, error='add', trend=None, seasonal='add', seasonal_periods=7, initialization_method='estimated')
                    fit = fit_checked(model, 'ets', fits, dict(configuration='ets_weekly_monthly', state=state, year=int(year),
                        training_end=str(end.date()), missing_past_filled=int(data[state].reindex(tr.index).isna().sum())))
                context = y.loc[training_start:origin-pd.Timedelta(days=1)]
                assert context.index.max() < origin
                # Parameters include the fitted initial states for this exact
                # training start. Keep that start when extending through origin.
                updated = ETSModel(context, error='add', trend=None, seasonal='add', seasonal_periods=7,
                    initialization_method='estimated').smooth(fit.params)
                predicted = np.asarray(updated.forecast(14))*100.
                pack_rows(rows, group[group.origin.eq(origin)], predicted, 'ets_weekly_monthly', scale)
                deployments.append(dict(configuration='ets_weekly_monthly', state=state, origin=str(origin.date()),
                    fitting_target_max=str((month-pd.Timedelta(days=1)).date()),
                    context_target_max=str((origin-pd.Timedelta(days=1)).date())))
            pd.DataFrame(rows).to_csv(out/'checkpoint.csv', index=False)
            dump(out/'fit_attempts.json', fits)
            pd.DataFrame(deployments).to_csv(out/'deployments.csv', index=False)
            print('ETS', state, year, 'completed', flush=True)
        d = pd.DataFrame(rows)
        assert np.isfinite(d.prediction).all()
        assert len(d) == len(cases)*3
        d.to_csv(out/'predictions.csv', index=False)
        dump(out/'run.json', dict(completed_utc=datetime.now(timezone.utc).isoformat(),
            rows=len(d), configurations=3, fit_attempts=len(fits), converged_fits=sum(x['converged'] for x in fits),
            deployment_tasks=len(deployments), seconds=time.perf_counter()-started,
            protocol_sha256=sha(OUT/'protocol.json'), predictions_sha256=sha(out/'predictions.csv')))
    except Exception:
        dump(out/'fit_attempts.json', fits)
        (out/'failure.txt').write_text(traceback.format_exc())
        if rows:
            pd.DataFrame(rows).to_csv(out/'checkpoint.csv', index=False)
        raise


def foundation(worker):
    import torch
    p, out, cases, data = setup(worker)
    torch.set_num_threads(p['threads'])
    torch.manual_seed(p['seed'])
    np.random.seed(p['seed'])
    if worker == 'chronos':
        from chronos import Chronos2Pipeline
        info = json.loads((ROOT/'results/mechanism_controls_v1/chronos_download.json').read_text())
        for item in info['files']:
            assert sha(item['path']) == item['sha256'], item['name']
        weights = next(x for x in info['files'] if x['name'] == 'model.safetensors')
        model = Chronos2Pipeline.from_pretrained(str(Path(weights['path']).parent), device_map='cpu', local_files_only=True)
        modes = ['calendar']
        levels = list(model.quantiles)
        weight_sha = weights['sha256']
    else:
        from timesfm3 import TimesFM3Evaluator, ModelConfig
        info = json.loads((ROOT/'results/second_model_audit_v1/weight_download.json').read_text())
        assert sha(info['path']) == info['sha256']
        model = TimesFM3Evaluator(ModelConfig(checkpoint_path=str(Path(info['path']).parent), device='cpu', per_core_batch_size=p['batch'], local_files_only=True))
        modes = ['history', 'calendar']
        levels = [x/10 for x in range(1, 10)]
        weight_sha = info['sha256']
    tasks = cases[['state', 'year', 'origin']].drop_duplicates().sort_values(['state', 'origin'])
    rows, batches, inputs_log, solo_audit = [], [], [], []
    started = time.perf_counter()

    def predict(inputs, mode):
        if worker == 'chronos':
            names = [f'dow_{i}' for i in range(7)] + [c for k in [1, 2, 3] for c in [f'sin_{k}', f'cos_{k}']]
            packed = [dict(target=target, past_covariates={name: cov[j, :730] for j, name in enumerate(names)},
                future_covariates={name: cov[j, 730:] for j, name in enumerate(names)}) for target, cov in inputs]
            outputs = model.predict(packed, prediction_length=14, batch_size=128, context_length=730, cross_learning=False)
            quantiles = [o[0].detach().cpu().numpy().T for o in outputs]
            return [(q[:, levels.index(.5)], q) for q in quantiles]
        kwargs = {} if mode == 'history' else dict(past_future_covariates=[x[1] for x in inputs])
        outputs = list(model.predict_batch([x[0] for x in inputs], horizon=14, return_quantiles=True, use_symmetric_averaging=False, **kwargs))
        return [(np.asarray(o.forecast).squeeze(), np.asarray(o.quantiles).squeeze()) for o in outputs]

    try:
        for mode in modes:
            for offset in range(0, len(tasks), p['batch']):
                group = list(tasks.iloc[offset:offset+p['batch']].itertuples(index=False))
                inputs = [build_input(data[t.state], t.state, t.origin, mode) for t in group]
                for task, (target, cov) in zip(group, inputs):
                    altered = data[task.state].copy()
                    altered.loc[task.origin:] = 1e12
                    tt, cc = build_input(altered, task.state, task.origin, mode)
                    np.testing.assert_array_equal(target, tt)
                    if cov is not None:
                        np.testing.assert_array_equal(cov, cc)
                    inputs_log.append(dict(mode=mode, state=task.state, origin=str(task.origin.date()),
                        target_sha256=hashlib.sha256(target.tobytes()).hexdigest(),
                        covariate_sha256=None if cov is None else hashlib.sha256(cov.tobytes()).hexdigest(),
                        last_context_date=str((task.origin-pd.Timedelta(days=1)).date()),
                        future_target_perturbation_invariant=True))
                tick = time.perf_counter()
                output = predict(inputs, mode)
                assert len(output) == len(inputs)
                if offset == 0:
                    for pair, batch_result in zip(inputs, output):
                        solo = predict([pair], mode)[0]
                        np.testing.assert_allclose(solo[0], batch_result[0], rtol=2e-4, atol=1e-3)
                        solo_audit.append(dict(mode=mode, max_abs_difference=float(np.max(abs(solo[0]-batch_result[0])))))
                    dump(out/'solo_batch_audit.json', solo_audit)
                for task, (point, quantiles) in zip(group, output):
                    assert point.shape == (14,) and quantiles.shape == (14, len(levels))
                    assert np.isfinite(point).all() and np.isfinite(quantiles).all()
                    selected = cases[cases.state.eq(task.state) & cases.origin.eq(task.origin)]
                    scale = scale_for(data, task.state, task.year)
                    for r in selected.itertuples(index=False):
                        j = r.horizon-1
                        rows.append(dict(family=r.family, state=r.state, year=r.year, origin=str(r.origin.date()),
                            date=str(r.date.date()), horizon=r.horizon, prediction=float(point[j]), actual=float(data.loc[r.date, r.state]),
                            mase_scale=scale, configuration=('chronos' if worker == 'chronos' else 'timesfm')+'_'+mode,
                            **{f'q_{int(round(level*1000)):03d}': float(v) for level, v in zip(levels, quantiles[j])}))
                batches.append(dict(mode=mode, offset=offset, tasks=len(group), seconds=time.perf_counter()-tick))
                pd.DataFrame(rows).to_csv(out/'checkpoint.csv', index=False)
                dump(out/'batches.json', batches)
                if offset % 40 == 0 or offset+len(group) == len(tasks):
                    print(worker, mode, offset+len(group), '/', len(tasks), flush=True)
        d = pd.DataFrame(rows)
        assert len(d) == len(cases)*len(modes)
        d.to_csv(out/'predictions.csv', index=False)
        dump(out/'inputs.json', inputs_log)
        qcols = [f'q_{int(round(level*1000)):03d}' for level in levels]
        dump(out/'run.json', dict(completed_utc=datetime.now(timezone.utc).isoformat(),
            configurations=len(modes), inference_tasks=len(tasks)*len(modes), scored_rows=len(d),
            native_quantile_crossings=int((np.diff(d[qcols].to_numpy(), axis=1)<0).sum()),
            weight_sha256=weight_sha, seconds=time.perf_counter()-started,
            protocol_sha256=sha(OUT/'protocol.json'), predictions_sha256=sha(out/'predictions.csv')))
    except Exception:
        (out/'failure.txt').write_text(traceback.format_exc())
        dump(out/'inputs.json', inputs_log)
        raise


def combine():
    if (OUT/'predictions.csv').exists():
        raise FileExistsError('Preserve completed comparison')
    p = json.loads((OUT/'protocol.json').read_text())
    assert sha(BASE/'predictions.csv') == p['input_hashes']['results/multifestival_cached_v1/predictions.csv']
    frames = [pd.read_csv(BASE/'predictions.csv')]
    for worker in ['classical', 'chronos', 'timesfm']:
        run = json.loads((OUT/worker/'run.json').read_text())
        assert sha(OUT/worker/'predictions.csv') == run['predictions_sha256']
        frames.append(pd.read_csv(OUT/worker/'predictions.csv'))
    d = pd.concat(frames, ignore_index=True)
    assert d.configuration.nunique() == 15
    assert not d.duplicated(['family', 'configuration']+KEY).any()
    reference = set(map(tuple, frames[0][['family']+KEY].drop_duplicates().values))
    for config, g in d.groupby('configuration'):
        assert set(map(tuple, g[['family']+KEY].values)) == reference, config
    assert np.isfinite(d[['prediction', 'actual', 'mase_scale']]).all().all()
    d.to_csv(OUT/'predictions.csv', index=False)
    metrics(d, OUT)
    dump(OUT/'run.json', dict(completed_utc=datetime.now(timezone.utc).isoformat(), configurations=15,
        scored_cases_per_configuration=len(reference), rows=len(d), protocol_sha256=sha(OUT/'protocol.json'),
        predictions_sha256=sha(OUT/'predictions.csv'), original_and_frozen_forecasts_unchanged=True))
    print('COMBINED', len(d), 'rows;15configurations,528cases/configuration')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['prepare', 'classical', 'chronos', 'timesfm', 'combine'])
    action = parser.parse_args().action
    if action in ['chronos', 'timesfm']:
        foundation(action)
    else:
        {'prepare': prepare, 'classical': classical, 'combine': combine}[action]()
