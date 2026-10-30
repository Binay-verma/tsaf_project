"""Nine fixed information/dimension controls on both pinned foundation models."""
from pathlib import Path
import argparse
import hashlib
import importlib.metadata
import json
import time
import numpy as np
import pandas as pd
from forecasting import ROOT, load_data, causal_fill
from calendar_controls import covariates

OUT = ROOT/'results/mechanism_controls_v1'


def construct(observed, frame, origin):
    past = observed.loc[:origin-pd.Timedelta(days=1)].tail(730)
    target = causal_fill(observed).reindex(past.index).to_numpy(dtype=np.float32)
    dates = pd.date_range(origin-pd.Timedelta(days=730), periods=744)
    cov = frame.reindex(dates).to_numpy(dtype=np.float32).T
    assert target.shape == (730,) and cov.shape[1] == 744
    assert np.isfinite(target).all() and np.isfinite(cov).all()
    return target, cov


def main():
    import torch
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', choices=['chronos2', 'timesfm3'], required=True)
    args = parser.parse_args()
    out = OUT/args.model
    out.mkdir(exist_ok=True)
    if (out/'checkpoint.csv').exists() or (out/'predictions.csv').exists():
        raise FileExistsError('Preserve prior/interrupted runs; use a new versioned experiment')
    protocol = json.loads((OUT/'protocol.json').read_text())
    base = json.loads((ROOT/'results/calendar_controls_v1/protocol.json').read_text())
    assert base['placebo'] == protocol['placebo']
    cases = pd.read_csv(OUT/'cases.csv', parse_dates=['origin', 'date'])
    assert hashlib.sha256((OUT/'cases.csv').read_bytes()).hexdigest() == protocol['cases_sha256']
    tasks = cases[['state', 'origin', 'year']].drop_duplicates().sort_values(['state', 'origin'])
    data = load_data('latest')
    frames = {s: covariates(data.index, s, base)[0] for s in protocol.get('states', list(data))}
    torch.set_num_threads(protocol['threads_per_process'])
    torch.manual_seed(42)
    np.random.seed(42)
    if args.model == 'chronos2':
        from chronos import Chronos2Pipeline
        metadata = json.loads((OUT/'chronos_download.json').read_text())
        weights = Path(next(x['path'] for x in metadata['files'] if x['name'] == 'model.safetensors'))
        model = Chronos2Pipeline.from_pretrained(str(weights.parent), device_map='cpu')
        levels = list(model.quantiles)
        weight_sha = next(x['sha256'] for x in metadata['files'] if x['name'] == 'model.safetensors')
    else:
        from timesfm3 import TimesFM3Evaluator, ModelConfig
        metadata = json.loads((ROOT/'results/second_model_audit_v1/weight_download.json').read_text())
        weights = Path(metadata['path'])
        model = TimesFM3Evaluator(ModelConfig(checkpoint_path=str(weights.parent), device='cpu',
            per_core_batch_size=protocol['batch'], local_files_only=True))
        levels = [i/10 for i in range(1, 10)]
        weight_sha = metadata['sha256']
    with weights.open('rb') as f:
        assert hashlib.file_digest(f, 'sha256').hexdigest() == weight_sha
    rows, logs = [], []
    started = time.perf_counter()
    try:
        for arm in protocol['arms']:
            for offset in range(0, len(tasks), protocol['batch']):
                group = list(tasks.iloc[offset:offset+protocol['batch']].itertuples(index=False))
                inputs = [construct(data[t.state], frames[t.state][arm], t.origin) for t in group]
                # Inputs are invariant to any changed unseen target observations.
                for task, (target, cov) in zip(group, inputs):
                    changed = data[task.state].copy()
                    changed.loc[task.origin:] = 1e12
                    tt, cc = construct(changed, frames[task.state][arm], task.origin)
                    np.testing.assert_array_equal(target, tt)
                    np.testing.assert_array_equal(cov, cc)
                tick = time.perf_counter()
                if args.model == 'chronos2':
                    packed = []
                    for (target, cov), task in zip(inputs, group):
                        names = list(frames[task.state][arm])
                        packed.append(dict(target=target,
                            past_covariates={name: cov[i, :730] for i, name in enumerate(names)},
                            future_covariates={name: cov[i, 730:] for i, name in enumerate(names)}))
                    output = model.predict(packed, prediction_length=14, batch_size=128,
                                           context_length=730, cross_learning=False)
                    quantiles = [q[0].detach().cpu().numpy().T for q in output]
                    points = [q[:, levels.index(.5)] for q in quantiles]
                else:
                    output = list(model.predict_batch([x[0] for x in inputs], horizon=14,
                        past_future_covariates=[x[1] for x in inputs], return_quantiles=True,
                        use_symmetric_averaging=False))
                    quantiles = [np.asarray(o.quantiles).squeeze() for o in output]
                    points = [np.asarray(o.forecast).squeeze() for o in output]
                assert len(points) == len(group)
                for task, point, q in zip(group, points, quantiles):
                    assert point.shape == (14,) and q.shape == (14, len(levels))
                    assert np.isfinite(point).all() and np.isfinite(q).all()
                    cutoff = pd.Timestamp(f'{task.year-1}-12-31')
                    tr = data[task.state].loc[cutoff-pd.Timedelta(days=729):cutoff]
                    scale = float((tr-tr.shift(7)).abs().mean())
                    for j in range(14):
                        date = task.origin+pd.Timedelta(days=j)
                        rows.append(dict(state=task.state, origin=task.origin, date=date,
                            year=task.year, horizon=j+1, arm=arm, model=args.model,
                            prediction=float(point[j]), actual=float(data.loc[date, task.state]),
                            mase_scale=scale, **{f'q_{int(round(level*1000)):03d}': float(v)
                                               for level, v in zip(levels, q[j])}))
                logs.append(dict(arm=arm, first_task=offset, n=len(group),
                    covariate_channels=inputs[0][1].shape[0], seconds=time.perf_counter()-tick))
                pd.DataFrame(rows).to_csv(out/'checkpoint.csv', index=False)
                (out/'batches.json').write_text(json.dumps(logs, indent=2)+'\n')
                print(args.model, arm, offset+len(group), '/', len(tasks), round(logs[-1]['seconds'], 2), flush=True)
        full = pd.DataFrame(rows)
        full.to_csv(out/'all_forecast_days.csv', index=False)
        d = full.merge(cases, on=['state', 'origin', 'date', 'year', 'horizon'], validate='many_to_one')
        assert len(d) == len(cases)*len(protocol['arms'])
        d.to_csv(out/'predictions.csv', index=False)
        (out/'run.json').write_text(json.dumps(dict(model=args.model, scored_rows=len(d),
            inference_tasks=len(tasks)*len(protocol['arms']), all_forecast_days=len(full),
            seconds=time.perf_counter()-started, levels=levels, weight_sha256=weight_sha,
            packages={p: importlib.metadata.version(p) for p in
                ['torch', 'numpy', 'pandas', 'transformers', 'chronos-forecasting', 'timesfm']},
            hashes={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in
                [Path(__file__), ROOT/'src/calendar_controls.py', OUT/'protocol.json', OUT/'cases.csv',
                 ROOT/'data/external/latest_state_energy_GWh.csv']}), indent=2)+'\n')
        print('COMPLETED', args.model, len(d), flush=True)
    except Exception as exc:
        (out/'failure.json').write_text(json.dumps(dict(error=repr(exc), completed_batches=len(logs)), indent=2)+'\n')
        raise


if __name__ == '__main__':
    main()
