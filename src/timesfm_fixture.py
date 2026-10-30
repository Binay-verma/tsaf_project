"""Pinned-weight, small CPU TimesFM3 API fixture; not a broad model benchmark."""
from pathlib import Path
import hashlib
import importlib.metadata
import json
import time
import numpy as np
import pandas as pd
from forecasting import ROOT, load_data, causal_fill
from extended_validation import features

OUT = ROOT/'results/second_model_audit_v1'


def build_input(observed, state, origin, mode, context=730):
    origin = pd.Timestamp(origin)
    target = causal_fill(observed).loc[:origin-pd.Timedelta(days=1)].tail(context).to_numpy(dtype=np.float32)
    assert len(target) == context and np.isfinite(target).all()
    if mode == 'history':
        return target, None
    cal, cols, _ = features(observed.index, state)
    names = cols['B_calendar' if mode == 'calendar' else 'D_regional_festival']
    dates = pd.date_range(origin-pd.Timedelta(days=context), periods=context+14)
    cov = cal.reindex(dates)[names].to_numpy(dtype=np.float32).T
    assert np.isfinite(cov).all() and cov.shape[1] == context+14
    return target, cov


def main():
    import torch
    from timesfm3 import TimesFM3Evaluator, ModelConfig
    protocol = json.loads((OUT/'fixture_protocol.json').read_text())
    if (OUT/'fixture_predictions.csv').exists():
        raise FileExistsError('Preserve this fixture')
    downloaded = json.loads((OUT/'weight_download.json').read_text())
    weights = Path(downloaded['path'])
    assert hashlib.file_digest(weights.open('rb'), 'sha256').hexdigest() == protocol['expected_sha256']
    torch.set_num_threads(protocol['torch_threads'])
    torch.manual_seed(42)
    np.random.seed(42)
    start = time.perf_counter()
    model = TimesFM3Evaluator(ModelConfig(checkpoint_path=str(weights.parent), device='cpu',
                              per_core_batch_size=1, local_files_only=True))
    data = load_data('latest')
    rows, tasks = [], []
    try:
        for state in protocol['states']:
            for origin in map(pd.Timestamp, protocol['origins']):
                tr = data[state].loc['2024-01-02':'2025-12-31']
                scale = float((tr-tr.shift(7)).abs().mean())
                for mode in protocol['modes']:
                    target, cov = build_input(data[state], state, origin, mode)
                    altered = data[state].copy()
                    altered.loc[origin:] = 1e12
                    altered_target, altered_cov = build_input(altered, state, origin, mode)
                    np.testing.assert_array_equal(target, altered_target)
                    if cov is not None:
                        np.testing.assert_array_equal(cov, altered_cov)
                    tick = time.perf_counter()
                    kwargs = {} if cov is None else dict(past_future_covariates=[cov])
                    output = list(model.predict_batch([target], horizon=14, return_quantiles=True,
                                   use_symmetric_averaging=False, **kwargs))
                    assert len(output) == 1
                    pred = np.asarray(output[0].forecast).squeeze()
                    quantiles = np.asarray(output[0].quantiles).squeeze()
                    assert pred.shape == (14,) and quantiles.shape == (14, 9)
                    assert np.isfinite(pred).all() and np.isfinite(quantiles).all()
                    tasks.append(dict(state=state, origin=str(origin.date()), mode=mode,
                        seconds=time.perf_counter()-tick, target_shape=list(target.shape),
                        covariate_shape=None if cov is None else list(cov.shape),
                        target_sha256=hashlib.sha256(target.tobytes()).hexdigest(),
                        covariate_sha256=None if cov is None else hashlib.sha256(cov.tobytes()).hexdigest()))
                    for j in range(14):
                        date = origin+pd.Timedelta(days=j)
                        rows.append(dict(state=state, origin=origin, date=date, horizon=j+1,
                            mode=mode, prediction=float(pred[j]), actual=float(data.loc[date, state]),
                            mase_scale=scale, **{f'q{k+1:02d}': float(v) for k, v in enumerate(quantiles[j])}))
                    pd.DataFrame(rows).to_csv(OUT/'fixture_checkpoint.csv', index=False)
                    (OUT/'fixture_tasks.json').write_text(json.dumps(tasks, indent=2)+'\n')
                    print('TimesFM fixture', state, origin.date(), mode, tasks[-1]['seconds'], flush=True)
        d = pd.DataFrame(rows)
        d.to_csv(OUT/'fixture_predictions.csv', index=False)
        crossing = int((np.diff(d[[f'q{i:02d}' for i in range(1, 10)]].to_numpy(), axis=1) < 0).sum())
        info = dict(tasks=len(tasks), forecast_days=len(d), quantile_values=len(d)*9,
            seconds=time.perf_counter()-start, native_adjacent_quantile_crossings=crossing,
            packages={n: importlib.metadata.version(n) for n in
                ['torch', 'timesfm', 'numpy', 'huggingface-hub', 'safetensors']},
            code_revision=protocol['code_revision'], weight_revision=protocol['weight_revision'],
            weight_sha256=downloaded['sha256'],
            hashes={str(f.relative_to(ROOT)): hashlib.sha256(f.read_bytes()).hexdigest()
                for f in [Path(__file__), OUT/'fixture_protocol.json',
                          ROOT/'data/external/latest_state_energy_GWh.csv']},
            warning='Small fixed API fixture; no broad superiority, festival or clean final-test claim')
        (OUT/'fixture_run.json').write_text(json.dumps(info, indent=2)+'\n')
        print(json.dumps(info, indent=2))
    except Exception as exc:
        (OUT/'fixture_failure.json').write_text(json.dumps({'error': repr(exc), 'completed_tasks': len(tasks)}, indent=2)+'\n')
        raise


if __name__ == '__main__':
    main()
