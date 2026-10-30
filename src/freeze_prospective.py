"""Freeze forecasts now; do not fetch outcomes or overwrite the forecast artifact."""
from pathlib import Path
import datetime
import hashlib
import json
import time
import numpy as np
import pandas as pd
from forecasting import ROOT, load_data
from robust_baselines import design_frame, fitting_cases, make_model
from timesfm_fixture import build_input

OUT = ROOT/'results/prospective_20261030_v1'


def main():
    import torch
    from timesfm3 import TimesFM3Evaluator, ModelConfig
    if (OUT/'predictions.csv').exists():
        raise FileExistsError('Frozen forecasts must never be overwritten')
    protocol = json.loads((OUT/'protocol.json').read_text())
    source_path = ROOT/protocol['context_snapshot']
    assert hashlib.sha256(source_path.read_bytes()).hexdigest() == protocol['context_sha256']
    issued = datetime.datetime.now(datetime.timezone.utc)
    assert issued.date() == datetime.date(2026, 10, 30), 'Issue date changed: version the protocol'
    data = load_data('latest')
    assert data.index.max() == pd.Timestamp('2026-10-28')
    origin = pd.Timestamp(protocol['first_unseen_origin'])
    # Extend CALENDAR rows only; future target labels stay missing.
    data = data.reindex(pd.date_range(data.index.min(), origin+pd.Timedelta(days=13)))
    config = json.loads((ROOT/'results/strong_refit_v1/protocol.json').read_text())
    weight = json.loads((ROOT/'results/second_model_audit_v1/weight_download.json').read_text())
    torch.set_num_threads(2)
    torch.manual_seed(42)
    np.random.seed(42)
    forecaster = TimesFM3Evaluator(ModelConfig(checkpoint_path=str(Path(weight['path']).parent),
                                             device='cpu', per_core_batch_size=1, local_files_only=True))
    rows, selection, fits = [], [], []
    for state in protocol['states']:
        observed = data[state]
        tr = observed.loc['2024-01-02':'2025-12-31']
        scale = float((tr-tr.shift(7)).abs().mean())
        for mode in ['history', 'calendar']:
            target, cov = build_input(observed, state, origin, mode)
            kwargs = {} if cov is None else dict(past_future_covariates=[cov])
            o = list(forecaster.predict_batch([target], horizon=14, return_quantiles=True,
                        use_symmetric_averaging=False, **kwargs))[0]
            pred, q = np.asarray(o.forecast).squeeze(), np.asarray(o.quantiles).squeeze()
            assert pred.shape == (14,) and q.shape == (14, 9)
            for j in range(14):
                rows.append(dict(state=state, model='timesfm3_'+mode, horizon=j+1,
                    prediction=float(pred[j]), **{f'q{k+1:02d}': float(v) for k, v in enumerate(q[j])}))
        for h in range(1, 15):
            frame, _ = design_frame(observed, state, h, 'rich_calendar')
            cutoff = pd.Timestamp('2025-12-31')
            vs = cutoff-pd.Timedelta(days=179)
            x, y, train_log = fitting_cases(frame, observed, h, vs-pd.Timedelta(days=1))
            vo = pd.date_range(vs, cutoff-pd.Timedelta(days=h-1))
            vd = vo+pd.Timedelta(days=h-1)
            vx, vy = frame.reindex(vo).to_numpy(), observed.reindex(vd).to_numpy()
            for name in ['ridge', 'lightgbm']:
                grid = ([dict(alpha=a) for a in config['ridge_alphas']] if name == 'ridge'
                        else config['lightgbm_grid'])
                losses = []
                for i, params in enumerate(grid):
                    fitted = make_model(name, params, config).fit(x, y)
                    loss = float(np.mean(abs(vy-fitted.predict(vx))))
                    losses.append((loss, i, params))
                    selection.append(dict(state=state, horizon=h, model=name, configuration=i,
                        validation_MAE=loss, parameters=params, training=train_log,
                        validation_target_max=str(vd.max().date())))
                loss, i, params = min(losses, key=lambda a: (a[0], a[1]))
                xx, yy, log = fitting_cases(frame, observed, h, '2026-09-30')
                fitted = make_model(name, params, config).fit(xx, yy)
                pred = float(fitted.predict(frame.reindex([origin]).to_numpy())[0])
                fits.append(dict(state=state, model=name, horizon=h, configuration=i,
                                 parameters=params, validation_MAE=loss, **log))
                rows.append(dict(state=state, model=name+'_rich_calendar_monthly', horizon=h, prediction=pred))
            last = observed.loc[:origin-pd.Timedelta(days=1)].dropna().tail(7).to_numpy()
            rows.append(dict(state=state, model='last_value', horizon=h, prediction=float(last[-1])))
            rows.append(dict(state=state, model='weekly_repeat', horizon=h, prediction=float(last[(h-1)%7])))
        print('Frozen', state, flush=True)
        for row in rows:
            if row['state'] == state:
                row.update(mase_scale=scale)
    d = pd.DataFrame(rows)
    d['origin'] = origin
    d['date'] = origin+pd.to_timedelta(d.horizon-1, unit='D')
    d['issued_utc'] = issued.isoformat()
    d['prospective_eligible'] = d.date.dt.date > issued.date()
    assert len(d) == 252 and np.isfinite(d.prediction).all()
    assert not d.duplicated(['state', 'model', 'horizon']).any()
    d.to_csv(OUT/'predictions.csv', index=False)
    (OUT/'selection.json').write_text(json.dumps(selection, indent=2)+'\n')
    (OUT/'fits.json').write_text(json.dumps(fits, indent=2)+'\n')
    info = dict(issued_utc=issued.isoformat(), rows=len(d), eligible_rows=int(d.prospective_eligible.sum()),
        eligible_start='2026-10-31', eligible_end='2026-11-11', selection_fits=len(selection),
        deployment_fits=len(fits), source_sha256=protocol['context_sha256'],
        code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        protocol_sha256=hashlib.sha256((OUT/'protocol.json').read_bytes()).hexdigest(),
        predictions_sha256=hashlib.sha256((OUT/'predictions.csv').read_bytes()).hexdigest(),
        weight_sha256=weight['sha256'], outcomes_fetched=False, scores_status='pending future observations')
    (OUT/'freeze.json').write_text(json.dumps(info, indent=2)+'\n')
    print(json.dumps(info, indent=2))


if __name__ == '__main__':
    main()
