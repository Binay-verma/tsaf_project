"""Fixed two-date data-availability sensitivity with recorded Git snapshots."""
from pathlib import Path
import gc
import hashlib
import json
import time
import numpy as np
import pandas as pd
from forecasting import ROOT, load_data, causal_fill
from extended_validation import features

OUT = ROOT/'results/vintage_sensitivity_v1'


def main():
    import torch
    torch.set_num_threads(1)
    torch.manual_seed(42)
    np.random.seed(42)
    if (OUT/'predictions.csv').exists():
        raise FileExistsError('Preserve completed sensitivity')
    protocol = json.loads((OUT/'protocol.json').read_text())
    vintages = json.loads((ROOT/'results/provenance_review_v1/git_vintage_audit.json').read_text())['snapshots']
    snapshots = {pd.Timestamp(v['issue_date_India']): v for v in vintages
                 if v.get('commit') and v.get('issue_date_India')}
    frozen = load_data('latest')
    rows, tasks = [], []
    for name in protocol['models']:
        if name == 'chronos2':
            from chronos import Chronos2Pipeline
            info = json.loads((ROOT/'results/mechanism_controls_v1/chronos_download.json').read_text())
            path = Path(next(x['path'] for x in info['files'] if x['name'] == 'model.safetensors'))
            model = Chronos2Pipeline.from_pretrained(str(path.parent), device_map='cpu')
        else:
            from timesfm3 import TimesFM3Evaluator, ModelConfig
            info = json.loads((ROOT/'results/second_model_audit_v1/weight_download.json').read_text())
            path = Path(info['path'])
            model = TimesFM3Evaluator(ModelConfig(checkpoint_path=str(path.parent), device='cpu',
                                                 per_core_batch_size=1, local_files_only=True))
        for issue in [pd.Timestamp('2026-09-01'), pd.Timestamp('2026-10-01')]:
            metadata = snapshots[issue]
            rawpath = Path('/workspace/source-vintage-cache')/(metadata['commit']+'.csv')
            assert hashlib.sha256(rawpath.read_bytes()).hexdigest() == metadata['sha256']
            raw = pd.read_csv(rawpath)
            raw.index = pd.to_datetime(raw.yyyymmdd.astype(str), format='%Y%m%d')
            for state in frozen:
                training = frozen[state].loc['2024-01-02':'2025-12-31']
                scale = float((training-training.shift(7)).abs().mean())
                for scenario in protocol['scenarios']:
                    if scenario == 'ideal_retrospective':
                        y = frozen[state].loc[:issue-pd.Timedelta(days=1)]
                    else:
                        y = raw[state+': EnergyMet'].where(raw[state+': EnergyMet'] > 0).asfreq('D')
                        y = y.loc[:y.last_valid_index()]
                    last = y.index.max()
                    origin = last+pd.Timedelta(days=1)
                    offset = int((issue-origin).days)
                    assert offset >= 0 and last < issue
                    horizon = 14+offset
                    target = causal_fill(y).tail(730).to_numpy(dtype=np.float32)
                    dates = pd.date_range(origin-pd.Timedelta(days=730), periods=730+horizon)
                    cal, cols, _ = features(dates, state)
                    cov = cal[cols['B_calendar']].to_numpy(dtype=np.float32).T
                    for mode in ['history', 'calendar']:
                        tick = time.perf_counter()
                        if name == 'chronos2':
                            inputs = target if mode == 'history' else dict(target=target,
                                past_covariates={c: cov[i, :730] for i, c in enumerate(cols['B_calendar'])},
                                future_covariates={c: cov[i, 730:] for i, c in enumerate(cols['B_calendar'])})
                            output = model.predict([inputs], prediction_length=horizon, context_length=730,
                                                   batch_size=128, cross_learning=False)[0]
                            pred = output[0, model.quantiles.index(.5)].detach().cpu().numpy()
                        else:
                            kwargs = {} if mode == 'history' else dict(past_future_covariates=[cov])
                            output = list(model.predict_batch([target], horizon=horizon,
                                use_symmetric_averaging=False, return_quantiles=True, **kwargs))[0]
                            pred = np.asarray(output.forecast).squeeze()
                        assert np.isfinite(pred).all() and len(pred) == horizon
                        tasks.append(dict(model=name, state=state, issue_date=str(issue.date()), mode=mode,
                            scenario=scenario, last_context_date=str(last.date()), first_unseen=str(origin.date()),
                            horizon_offset=offset, raw_commit=metadata['commit'] if scenario != 'ideal_retrospective' else None,
                            seconds=time.perf_counter()-tick))
                        for j in range(14):
                            date = issue+pd.Timedelta(days=j)
                            rows.append(dict(model=name, state=state, issue=issue, date=date, lead=j+1,
                                first_unseen=origin, forecast_lead=j+1+offset, scenario=scenario, mode=mode,
                                prediction=float(pred[j+offset]), actual=float(frozen.loc[date, state]), mase_scale=scale))
                        print(name, state, issue.date(), scenario, mode, offset, flush=True)
            pd.DataFrame(rows).to_csv(OUT/'checkpoint.csv', index=False)
        del model
        gc.collect()
    d = pd.DataFrame(rows)
    d.to_csv(OUT/'predictions.csv', index=False)
    d['scaled'] = abs(d.actual-d.prediction)/d.mase_scale
    d.groupby(['model', 'state', 'issue', 'mode', 'scenario']).scaled.mean().reset_index().to_csv(
        OUT/'metrics_state_issue.csv', index=False)
    d.groupby(['model', 'state', 'issue', 'mode', 'scenario']).scaled.mean().groupby(
        ['model', 'mode', 'scenario']).mean().reset_index().to_csv(OUT/'metrics_macro.csv', index=False)
    (OUT/'tasks.json').write_text(json.dumps(tasks, indent=2)+'\n')
    (OUT/'run.json').write_text(json.dumps(dict(rows=len(d), tasks=len(tasks),
        protocol_sha256=hashlib.sha256((OUT/'protocol.json').read_bytes()).hexdigest(),
        code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        warning='Retrospective two-date availability sensitivity; not future scoring or exhaustive vintage reconstruction'), indent=2)+'\n')
    print('COMPLETE', len(d), flush=True)


if __name__ == '__main__':
    main()
