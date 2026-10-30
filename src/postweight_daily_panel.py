"""Matched daily retrospective panel after both pinned weight uploads."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
import traceback
import numpy as np
import pandas as pd
from forecasting import ROOT, load_data, causal_fill
from festival_feature_design import sha, dump
from festival_feature_experiment import scale
from robust_baselines import design_frame, fitting_cases, make_model
from extended_validation import features

OUT = ROOT/'results/postweight_daily_v1'
STATES = ['Delhi', 'Karnataka', 'Maharashtra']


def inputs(observed, state, origin, mode):
    history = causal_fill(observed).loc[:origin-pd.Timedelta(days=1)].tail(730).to_numpy(dtype=np.float32)
    dates = pd.date_range(origin-pd.Timedelta(days=730), periods=744)
    if mode == 'history':
        cov = np.empty((0, 744), dtype=np.float32)
    else:
        x, cols, _ = features(dates, state)
        cov = x[cols['B_calendar']].to_numpy(dtype=np.float32).T
    assert history.shape == (730,) and cov.shape == ((0 if mode == 'history' else 13), 744)
    assert np.isfinite(history).all() and np.isfinite(cov).all()
    return history, cov


def prepare():
    if OUT.exists():
        raise FileExistsError('Preserve panel; version a fresh study')
    data = load_data('latest')
    rows = []
    for state in STATES:
        for target in pd.date_range('2026-09-15', '2026-10-28'):
            assert pd.notna(data.loc[target, state]) and data.loc[target, state] > 0
            for h in [1, 7, 14]:
                origin = target-pd.Timedelta(days=h-1)
                assert origin >= pd.Timestamp('2026-09-02')
                rows.append(dict(state=state, year=2026, origin=str(origin.date()), date=str(target.date()), horizon=h))
    cases = pd.DataFrame(rows)
    assert len(cases) == 396 and len(cases[['state', 'origin']].drop_duplicates()) == 171
    OUT.mkdir(parents=True)
    cases.to_csv(OUT/'cases.csv', index=False)
    paths = ['src/postweight_daily_panel.py', 'src/test_postweight_panel.py', 'src/robust_baselines.py',
        'src/forecasting.py', 'src/extended_validation.py', 'src/festival_feature_experiment.py',
        'data/external/latest_state_energy_GWh.csv', 'results/strong_refit_v1/selected.csv',
        'results/strong_refit_v1/protocol.json', 'results/strong_refit_v1/predictions.csv',
        'results/stable_tree_refit_v2/selected.csv', 'results/stable_tree_refit_v2/protocol.json',
        'results/stable_tree_refit_v2/predictions.csv',
        'results/mechanism_controls_v1/chronos_download.json', 'results/second_model_audit_v1/weight_download.json',
        'results/pooled_festival_v1/protected_prior_files.json']
    dump(OUT/'protocol.json', dict(experiment=OUT.name, created_utc=datetime.now(timezone.utc).isoformat(),
        status='Exploratory retrospective daily audit on previously inspected2026source; protocol fixed before fresh panel inference. Not an untouched test, source-independent replication or external preregistration.',
        target='Recorded daily energy met/supplied inGWh, same frozen source ending28October2026. No new actual retrieval.',
        target_dates=['2026-09-15', '2026-10-28'], first_origin='2026-09-02',
        cases_per_configuration=396, state_origin_tasks_per_foundation_mode=171,
        configurations=['chronos_history', 'chronos_calendar', 'timesfm_history', 'timesfm_calendar',
            'ridge_calendar_monthly', 'lightgbm_calendar_monthly', 'last_value', 'weekly_repeat'],
        chronology='Every scored target and origin postdates both audited actual weight uploads (Chronos30October2025; TimesFM24August2026) and the documented31August2026TimesFM announcement. This rules out direct inclusion of genuinely later targets in unchanged weights, conditional on source dates; not exact training cutoff, proxy clearance or untouched research outcomes.',
        availability='Ideal retrospective past-data availability: each context ends origin-1. Historical lag/revisions are not reconstructed. Date-vintage sensitivity is a separate earlier study. Calendar covariates are only13deterministic weekday/Fourier channels, no uncertified2026festival dates or future weather.',
        fitting='Local rich-calendar monthly models reuse their original pre2026selected parameters, same730day fitting-origin window with horizon-purged labels and float32 tree interface. No panel-based selection/refit/feature tuning. Each compares to original saved outputs where earlier full-horizon coverage overlaps.',
        foundation='Both pinned local-weight models, history/calendar, no fine-tuning.730day contexts,14day output,batch4,2threads,seed42; Chronos cross_learningFalse, TimesFM symmetricFalse; solo/batch and future-target perturbation audits. Only registered historical target cases are scored/saved, never new November actuals or modifications of the prospective freeze.',
        simple='Last recorded/causally-filled past value; weekly repeat cycles the last7observed-context values to each individual lead. Same source labels/scale/cases.',
        point_metrics='MAE perstate, original pre2026weekly-difference scale, MASE equal across3states perlead. Leads1/7/14are individual target days. Identical44target dates for each state/lead/configuration; no forecast-success intersection.',
        native_probability='Common0.1–0.9quantiles, mean scaled pinball, unmodified central80%coverage/width/interval score and one-intervalWIS plus native median. No calibration/sorting/clipping. All-native adjacent crossings inventoried; invalid endpoints remain explicit and propagate undefined interval summaries.',
        limits=['Previously inspected targets remain exploratory despite post-weight chronology', 'One source,44targetdates,3relatedstates and correlated overlapping horizons',
            'No added-festival representation test or full-year two-model claim', 'No independent human approval, source reuse grant, complete amendments or prospective score'],
        context=730, horizon=14, batch=4, threads=2, seed=42,
        input_hashes={f: sha(ROOT/f) for f in paths}, cases_sha256=sha(OUT/'cases.csv')))
    print('FROZEN396cases/config x8configs =3168rows;684foundation context tasks')


def setup(worker):
    p = json.loads((OUT/'protocol.json').read_text())
    for f, h in p['input_hashes'].items():
        assert sha(ROOT/f) == h, f
    assert sha(OUT/'cases.csv') == p['cases_sha256']
    out = OUT/worker; out.mkdir(exist_ok=True)
    if (out/'started.json').exists():
        raise FileExistsError('Preserve worker, including partial/failed outputs')
    dump(out/'started.json', dict(worker=worker, started_utc=datetime.now(timezone.utc).isoformat()))
    return p, out, pd.read_csv(OUT/'cases.csv', parse_dates=['date', 'origin']), load_data('latest')


def classical():
    p, out, cases, data = setup('classical')
    rows, fits, checks = [], [], []
    start = time.perf_counter()
    try:
        for (state, h), group in cases.groupby(['state', 'horizon']):
            history = causal_fill(data[state])
            for name in ['last_value', 'weekly_repeat']:
                a = group.copy()
                lag = 1 if name == 'last_value' else 7-((int(h)-1) % 7)
                a['prediction'] = [history.loc[o-pd.Timedelta(days=lag)] for o in group.origin]
                a['configuration'] = name; rows.append(a)
            base, _ = design_frame(data[state], state, int(h), 'rich_calendar')
            for model_name in ['ridge', 'lightgbm']:
                old = ROOT/'results'/('strong_refit_v1' if model_name == 'ridge' else 'stable_tree_refit_v2')
                selected = pd.read_csv(old/'selected.csv')
                selected = selected[selected.state.eq(state) & selected.year.eq(2026) & selected.model.eq(model_name) & selected['mode'].eq('rich_calendar') & selected.horizon.eq(h)]
                assert len(selected) == 1
                params = json.loads(selected.parameters.iloc[0]); fixed = json.loads((old/'protocol.json').read_text())
                frame = base.astype(np.float32) if model_name == 'lightgbm' else base
                chunks = []
                for month, segment in group.groupby(group.origin.dt.to_period('M')):
                    refit = month.start_time; cutoff = refit-pd.Timedelta(days=1)
                    xx, yy, log = fitting_cases(frame, data[state], int(h), cutoff)
                    assert pd.Timestamp(log['training_target_max']) < refit <= segment.origin.min()
                    query = frame.reindex(pd.DatetimeIndex(segment.origin)).to_numpy()
                    prediction = make_model(model_name, params, fixed).fit(xx, yy).predict(query)
                    a = segment.copy(); a['prediction'] = prediction; a['configuration'] = model_name+'_calendar_monthly'
                    chunks.append(a)
                    fits.append(dict(state=state, horizon=int(h), model=model_name, refit=str(refit.date()), parameters=params,
                        training_X_sha256=hashlib.sha256(xx.tobytes()).hexdigest(), training_y_sha256=hashlib.sha256(yy.tobytes()).hexdigest(), **log))
                a = pd.concat(chunks, ignore_index=True); rows.append(a)
                old_d = pd.read_csv(old/'predictions.csv', parse_dates=['date', 'origin'])
                old_d = old_d[old_d.state.eq(state) & old_d.year.eq(2026) & old_d.model.eq(model_name) & old_d['mode'].eq('rich_calendar') & old_d.schedule.eq('monthly') & old_d.horizon.eq(h)]
                common = a.merge(old_d[['state', 'origin', 'date', 'horizon', 'prediction']], on=['state', 'origin', 'date', 'horizon'], suffixes=('_new', '_old'), validate='one_to_one')
                assert len(common) == (group.origin <= pd.Timestamp('2026-10-15')).sum()
                np.testing.assert_allclose(common.prediction_new, common.prediction_old, rtol=1e-9, atol=1e-7)
                checks.append(dict(state=state, horizon=int(h), model=model_name, common_rows=len(common), maxdifference=float(abs(common.prediction_new-common.prediction_old).max())))
            print('classical', state, h, 'complete', flush=True)
        d = pd.concat(rows, ignore_index=True)
        d['actual'] = [data.loc[r.date, r.state] for r in d.itertuples(index=False)]
        d['mase_scale'] = [scale(data, r.state, 2026) for r in d.itertuples(index=False)]
        assert len(d) == 396*4 and np.isfinite(d.prediction).all()
        d.to_csv(out/'predictions.csv', index=False); dump(out/'fit_log.json', fits); dump(out/'baseline_reproduction.json', checks)
        dump(out/'run.json', dict(status='completed', rows=len(d), fits=len(fits), seconds=time.perf_counter()-start,
            protocol_sha256=sha(OUT/'protocol.json'), predictions_sha256=sha(out/'predictions.csv')))
    except Exception:
        (out/'failure.txt').write_text(traceback.format_exc()); dump(out/'fit_log.json', fits)
        raise


def foundation(worker):
    import torch
    p, out, cases, data = setup(worker)
    torch.set_num_threads(p['threads']); torch.manual_seed(p['seed']); np.random.seed(p['seed'])
    if worker == 'chronos':
        from chronos import Chronos2Pipeline
        identity = json.loads((ROOT/'results/mechanism_controls_v1/chronos_download.json').read_text())
        for r in identity['files']:
            assert sha(r['path']) == r['sha256']
        weight = next(r for r in identity['files'] if r['name'] == 'model.safetensors')
        model = Chronos2Pipeline.from_pretrained(str(Path(weight['path']).parent), device_map='cpu', local_files_only=True)
        levels = list(model.quantiles); weight_sha = weight['sha256']
    else:
        from timesfm3 import TimesFM3Evaluator, ModelConfig
        identity = json.loads((ROOT/'results/second_model_audit_v1/weight_download.json').read_text())
        assert sha(identity['path']) == identity['sha256']
        model = TimesFM3Evaluator(ModelConfig(checkpoint_path=str(Path(identity['path']).parent), device='cpu', per_core_batch_size=p['batch'], local_files_only=True))
        levels = [i/10 for i in range(1, 10)]; weight_sha = identity['sha256']
    tasks = cases[['state', 'origin']].drop_duplicates().sort_values(['state', 'origin'])
    assert len(tasks) == 171
    rows, logs, solo, batches = [], [], [], []
    start = time.perf_counter()

    def predict(pairs, mode):
        if worker == 'chronos':
            names = [f'dow_{k}' for k in range(7)]+[c for k in [1, 2, 3] for c in [f'sin_{k}', f'cos_{k}']]
            packed = [dict(target=t) if mode == 'history' else dict(target=t,
                past_covariates={n: c[j, :730] for j, n in enumerate(names)}, future_covariates={n: c[j, 730:] for j, n in enumerate(names)}) for t, c in pairs]
            output = model.predict(packed, prediction_length=14, batch_size=128, context_length=730, cross_learning=False)
            quantiles = [x[0].detach().cpu().numpy().T for x in output]
            return [(q[:, levels.index(.5)], q) for q in quantiles]
        kw = {} if mode == 'history' else dict(past_future_covariates=[x[1] for x in pairs])
        output = list(model.predict_batch([x[0] for x in pairs], horizon=14, return_quantiles=True, use_symmetric_averaging=False, **kw))
        return [(np.asarray(x.forecast).squeeze(), np.asarray(x.quantiles).squeeze()) for x in output]

    try:
        for mode in ['history', 'calendar']:
            for offset in range(0, len(tasks), p['batch']):
                group = list(tasks.iloc[offset:offset+p['batch']].itertuples(index=False))
                pairs = [inputs(data[t.state], t.state, t.origin, mode) for t in group]
                for task, (target, cov) in zip(group, pairs):
                    changed = data[task.state].copy(); changed.loc[task.origin:] = 1e12
                    tt, cc = inputs(changed, task.state, task.origin, mode)
                    np.testing.assert_array_equal(tt, target); np.testing.assert_array_equal(cc, cov)
                    logs.append(dict(state=task.state, origin=str(task.origin.date()), mode=mode,
                        context_end=str((task.origin-pd.Timedelta(days=1)).date()), feature_count=len(cov),
                        target_sha256=hashlib.sha256(target.tobytes()).hexdigest(), covariate_sha256=hashlib.sha256(cov.tobytes()).hexdigest(),
                        future_target_perturbation_invariant=True))
                tick = time.perf_counter(); output = predict(pairs, mode)
                if offset == 0:
                    for pair, result in zip(pairs, output):
                        one = predict([pair], mode)[0]
                        np.testing.assert_allclose(one[0], result[0], rtol=2e-4, atol=1e-3)
                        solo.append(dict(mode=mode, max_difference=float(abs(one[0]-result[0]).max())))
                for task, (point, quantiles) in zip(group, output):
                    assert point.shape == (14,) and quantiles.shape == (14, len(levels))
                    assert np.isfinite(point).all() and np.isfinite(quantiles).all()
                    for r in cases[cases.state.eq(task.state) & cases.origin.eq(task.origin)].itertuples(index=False):
                        rows.append(dict(state=r.state, year=2026, origin=str(r.origin.date()), date=str(r.date.date()), horizon=int(r.horizon),
                            configuration=worker+'_'+mode, actual=float(data.loc[r.date, r.state]), mase_scale=scale(data, r.state, 2026),
                            prediction=float(point[r.horizon-1]), **{f'q_{int(round(q*1000)):03d}': float(x) for q, x in zip(levels, quantiles[r.horizon-1])}))
                batches.append(dict(mode=mode, offset=offset, tasks=len(group), seconds=time.perf_counter()-tick))
                pd.DataFrame(rows).to_csv(out/'checkpoint.csv', index=False); dump(out/'inputs.json', logs)
                dump(out/'solo_batch_audit.json', solo); dump(out/'batches.json', batches)
                print(worker, mode, offset+len(group), '/', len(tasks), flush=True)
        d = pd.DataFrame(rows); assert len(d) == 396*2
        d.to_csv(out/'predictions.csv', index=False)
        qcols = [f'q_{int(round(q*1000)):03d}' for q in levels]
        dump(out/'run.json', dict(status='completed', rows=len(d), inference_tasks=len(logs), seconds=time.perf_counter()-start,
            native_quantile_crossings=int((np.diff(d[qcols].to_numpy(), axis=1)<0).sum()), weight_sha256=weight_sha,
            protocol_sha256=sha(OUT/'protocol.json'), predictions_sha256=sha(out/'predictions.csv')))
    except Exception:
        (out/'failure.txt').write_text(traceback.format_exc()); dump(out/'inputs.json', logs)
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('action', choices=['prepare', 'classical', 'chronos', 'timesfm'])
    action = parser.parse_args().action
    if action == 'prepare': prepare()
    elif action == 'classical': classical()
    else: foundation(action)
