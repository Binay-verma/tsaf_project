"""Versioned inference-only engine for pure calendar_encoding_v1; parents remain frozen.

Changes: registered task count; original full-daily calendar references.
"""
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


def foundation(worker):
    import torch
    from calendar_encoding_study import encoded_input, feature_names
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
    tasks = cases[['state', 'year', 'origin']].drop_duplicates().sort_values(['state', 'origin'])
    assert len(tasks) == p['expected_tasks']
    rows, inputs_log, batches, solo_audit = [], [], [], []
    started = time.perf_counter()

    def predict(inputs, names):
        if worker == 'chronos':
            packed = [dict(target=target, past_covariates={name: cov[i, :730] for i, name in enumerate(names)},
                future_covariates={name: cov[i, 730:] for i, name in enumerate(names)}) if names else dict(target=target) for target, cov in inputs]
            output = model.predict(packed, prediction_length=14, batch_size=128, context_length=730, cross_learning=False)
            qq = [q[0].detach().cpu().numpy().T for q in output]
            return [(q[:, levels.index(.5)], q) for q in qq]
        kwargs = dict(past_future_covariates=[x[1] for x in inputs]) if names else {}
        output = list(model.predict_batch([x[0] for x in inputs], horizon=14,
            return_quantiles=True, use_symmetric_averaging=False, **kwargs))
        return [(np.asarray(x.forecast).squeeze(), np.asarray(x.quantiles).squeeze()) for x in output]

    try:
        for arm in ARMS:
            for offset in range(0, len(tasks), p['batch']):
                group = list(tasks.iloc[offset:offset+p['batch']].itertuples(index=False))
                encoded = [encoded_input(data[t.state], t.state, arm, t.origin) for t in group]
                inputs = [x[:2] for x in encoded]
                names = feature_names(arm)
                for task, (target, cov), (_, _, diagnostics) in zip(group, inputs, encoded):
                    changed = data[task.state].copy(); changed.loc[task.origin:] = 1e12
                    tt, cc, _ = encoded_input(changed, task.state, arm, task.origin)
                    np.testing.assert_array_equal(target, tt); np.testing.assert_array_equal(cov, cc)
                    inputs_log.append(dict(arm=arm, state=task.state, origin=str(task.origin.date()),
                        target_sha256=hashlib.sha256(target.tobytes()).hexdigest(), covariate_sha256=hashlib.sha256(cov.tobytes()).hexdigest(),
                        feature_count=cov.shape[0], context_start=str((task.origin-pd.Timedelta(days=730)).date()),
                        context_end=str((task.origin-pd.Timedelta(days=1)).date()), future_target_perturbation_invariant=True,
                        past_nonzero_counts=np.count_nonzero(cov[:, :730], axis=1).astype(int).tolist(), encoding_diagnostics=diagnostics))
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


