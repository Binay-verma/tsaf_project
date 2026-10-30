"""Exact-case historical event replication with pinned TimesFM3 weights."""
from pathlib import Path
import hashlib
import json
import time
import numpy as np
import pandas as pd
from forecasting import ROOT, load_data
from timesfm_fixture import build_input

OUT = ROOT/'results/timesfm_matched_events_v1'


def main():
    import torch
    from timesfm3 import TimesFM3Evaluator, ModelConfig
    if (OUT/'predictions.csv').exists() or (OUT/'checkpoint.csv').exists():
        raise FileExistsError('Preserve interrupted/completed results; version a new run')
    protocol = json.loads((OUT/'protocol.json').read_text())
    cases = pd.read_csv(OUT/'cases.csv', parse_dates=['origin', 'date'])
    assert hashlib.sha256((OUT/'cases.csv').read_bytes()).hexdigest() == protocol['cases_sha256']
    tasks = cases[['state', 'origin', 'year']].drop_duplicates().sort_values(['state', 'origin'])
    download = json.loads((ROOT/'results/second_model_audit_v1/weight_download.json').read_text())
    weights = Path(download['path'])
    with weights.open('rb') as f:
        assert hashlib.file_digest(f, 'sha256').hexdigest() == download['sha256']
    torch.set_num_threads(protocol['torch_threads'])
    torch.manual_seed(42)
    np.random.seed(42)
    data = load_data('latest')
    model = TimesFM3Evaluator(ModelConfig(checkpoint_path=str(weights.parent), device='cpu',
                                         per_core_batch_size=protocol['batch'], local_files_only=True))
    rows, batch_audit = [], []
    start = time.perf_counter()
    for mode in protocol['modes']:
        for offset in range(0, len(tasks), protocol['batch']):
            group = list(tasks.iloc[offset:offset+protocol['batch']].itertuples(index=False))
            inputs = [build_input(data[t.state], t.state, t.origin, mode) for t in group]
            kwargs = {} if mode == 'history' else dict(past_future_covariates=[x[1] for x in inputs])
            tick = time.perf_counter()
            outputs = list(model.predict_batch([x[0] for x in inputs], horizon=14,
                            return_quantiles=True, use_symmetric_averaging=False, **kwargs))
            assert len(outputs) == len(group)
            if offset == 0:
                # Verify no cross-sample mixing via the documented batched API.
                maxdiff = 0.
                for pair, output in zip(inputs, outputs):
                    kw = {} if pair[1] is None else dict(past_future_covariates=[pair[1]])
                    solo = list(model.predict_batch([pair[0]], horizon=14, return_quantiles=True,
                                use_symmetric_averaging=False, **kw))[0]
                    a, b = np.asarray(output.forecast), np.asarray(solo.forecast)
                    np.testing.assert_allclose(a, b, rtol=2e-4, atol=1e-3)
                    maxdiff = max(maxdiff, float(np.max(abs(a-b))))
                batch_audit.append(dict(mode=mode, compared_tasks=len(inputs), max_abs_difference=maxdiff,
                                        tolerance='rtol2e-4 atol1e-3 (floating point batching)'))
                (OUT/'batch_audit.json').write_text(json.dumps(batch_audit, indent=2)+'\n')
            for task, output in zip(group, outputs):
                pred = np.asarray(output.forecast).squeeze()
                q = np.asarray(output.quantiles).squeeze()
                assert pred.shape == (14,) and q.shape == (14, 9)
                assert np.isfinite(pred).all() and np.isfinite(q).all()
                cutoff = pd.Timestamp(f'{task.year-1}-12-31')
                tr = data[task.state].loc[cutoff-pd.Timedelta(days=729):cutoff]
                scale = float((tr-tr.shift(7)).abs().mean())
                for j in range(14):
                    date = task.origin+pd.Timedelta(days=j)
                    rows.append(dict(state=task.state, origin=task.origin, date=date, year=task.year,
                        horizon=j+1, mode=mode, prediction=float(pred[j]),
                        actual=float(data.loc[date, task.state]), mase_scale=scale,
                        **{f'q{k+1:02d}': float(v) for k, v in enumerate(q[j])}))
            pd.DataFrame(rows).to_csv(OUT/'checkpoint.csv', index=False)
            print('Matched TimesFM', mode, offset+len(group), '/', len(tasks),
                  round(time.perf_counter()-tick, 2), 'seconds', flush=True)
    all_days = pd.DataFrame(rows)
    all_days.to_csv(OUT/'all_forecast_days.csv', index=False)
    d = all_days.merge(cases, on=['state', 'origin', 'date', 'year', 'horizon'], validate='many_to_one')
    assert len(d) == len(cases)*len(protocol['modes'])
    assert not d.duplicated(['state', 'origin', 'horizon', 'mode']).any()
    d.to_csv(OUT/'predictions.csv', index=False)
    d['ae'] = abs(d.actual-d.prediction)
    d['scaled'] = d.ae/d.mase_scale
    d['coverage80'] = ((d.actual >= d.q01) & (d.actual <= d.q09)).astype(float)
    d['scaled_width80'] = (d.q09-d.q01)/d.mase_scale
    pb = []
    for i in range(1, 10):
        e = d.actual-d[f'q{i:02d}']
        pb.append(np.maximum((i/10)*e, (i/10-1)*e)/d.mase_scale)
    d['scaled_mean_pinball'] = np.mean(pb, axis=0)
    metrics = d.groupby(['state', 'year', 'horizon', 'mode']).agg(MASE=('scaled', 'mean'),
        MAE_GWh=('ae', 'mean'), coverage80=('coverage80', 'mean'),
        scaled_width80=('scaled_width80', 'mean'), scaled_mean_pinball=('scaled_mean_pinball', 'mean'),
        n=('ae', 'size')).reset_index()
    metrics.to_csv(OUT/'metrics_state_year.csv', index=False)
    metrics.groupby(['year', 'horizon', 'mode'])[['MASE', 'coverage80', 'scaled_width80',
        'scaled_mean_pinball']].mean().reset_index().to_csv(OUT/'metrics_macro.csv', index=False)
    info = dict(scored_rows=len(d), independent_tasks=len(tasks)*3, all_forecast_days=len(all_days),
        seconds=time.perf_counter()-start, native_quantile_crossings=int((np.diff(
            d[[f'q{i:02d}' for i in range(1, 10)]].to_numpy(), axis=1) < 0).sum()),
        weight_sha256=download['sha256'],
        hashes={str(f.relative_to(ROOT)): hashlib.sha256(f.read_bytes()).hexdigest() for f in
                [Path(__file__), ROOT/'src/timesfm_fixture.py', OUT/'protocol.json', OUT/'cases.csv']},
        warning='Historical overlap-uncertain exploratory event comparison; no prospective score or provenance mechanism claim')
    (OUT/'run.json').write_text(json.dumps(info, indent=2)+'\n')
    print(json.dumps(info, indent=2))


if __name__ == '__main__':
    main()
