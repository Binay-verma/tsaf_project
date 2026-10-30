"""Forward-year regression-region transfer with permitted historical context."""
from pathlib import Path
import hashlib
import json
import time
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from forecasting import ROOT, STATES, load_data
from robust_baselines import design_frame, fitting_cases, evaluation_origins, score_predictions

OUT = ROOT/'results/regional_transfer_v1'


def fit_transfer(data, held, year, horizon, mode, arm):
    cutoff = pd.Timestamp(f'{year-1}-12-31')
    train_states = ([held] if arm == 'local' else
                    [s for s in STATES if s != held] if arm == 'leave_region_out' else list(STATES))
    if arm == 'leave_region_out':
        assert held not in train_states
    normalizers, frames, targets = {}, {}, {}
    for state in STATES:
        tr = data[state].loc[cutoff-pd.Timedelta(days=729):cutoff]
        center, scale = float(tr.mean()), float(tr.std())
        assert np.isfinite(center) and np.isfinite(scale) and scale > 0
        normalizers[state] = dict(center=center, scale=scale)
        targets[state] = (data[state]-center)/scale
        frames[state], _ = design_frame(targets[state], state, horizon, mode)
    xs, ys, logs = [], [], []
    for state in train_states:
        x, y, log = fitting_cases(frames[state], targets[state], horizon, cutoff)
        xs.append(x)
        ys.append(y)
        logs.append(dict(state=state, **log))
    fitted = make_pipeline(StandardScaler(), Ridge(alpha=10)).fit(np.concatenate(xs), np.concatenate(ys))
    return fitted, frames[held], normalizers, logs


def main():
    if (OUT/'predictions.csv').exists():
        raise FileExistsError('Preserve this run')
    start = time.perf_counter()
    p = json.loads((OUT/'protocol.json').read_text())
    data = load_data('latest')
    rows, logs = [], []
    for held in STATES:
        for year in p['years']:
            cutoff = pd.Timestamp(f'{year-1}-12-31')
            tr = data[held].loc[cutoff-pd.Timedelta(days=729):cutoff]
            mase = float((tr-tr.shift(7)).abs().mean())
            origins = evaluation_origins(year, data.index)
            for h in p['leads']:
                dates = origins+pd.Timedelta(days=h-1)
                for mode in p['modes']:
                    _, event = design_frame(data[held], held, h, mode)
                    for arm in p['arms']:
                        tick = time.perf_counter()
                        model, frame, norms, training = fit_transfer(data, held, year, h, mode, arm)
                        assert all(pd.Timestamp(log['training_target_max']) < origins.min() for log in training)
                        pred = model.predict(frame.reindex(origins).to_numpy())
                        pred = pred*norms[held]['scale']+norms[held]['center']
                        rows.append(pd.DataFrame(dict(state=held, year=year, model='ridge', mode=mode,
                            arm=arm, horizon=h, origin=origins, date=dates, prediction=pred,
                            actual=data[held].reindex(dates).to_numpy(),
                            event=event.reindex(dates).astype(int).to_numpy(), mase_scale=mase)))
                        logs.append(dict(held=held, year=year, horizon=h, mode=mode, arm=arm,
                            training_states=[log['state'] for log in training], training=training,
                            normalizers=norms, seconds=time.perf_counter()-tick))
            pd.concat(rows).to_csv(OUT/'checkpoint_predictions.csv', index=False)
            (OUT/'fits.json').write_text(json.dumps(logs, indent=2)+'\n')
            print('Completed transfer', held, year, flush=True)
    d = pd.concat(rows, ignore_index=True)
    d.to_csv(OUT/'predictions.csv', index=False)
    checks = score_predictions(d, OUT, ['model', 'mode', 'arm'])
    info = dict(rows=len(d), fits=len(logs), seconds=time.perf_counter()-start, checks=checks,
        hashes={str(f.relative_to(ROOT)): hashlib.sha256(f.read_bytes()).hexdigest() for f in
            [Path(__file__), ROOT/'src/robust_baselines.py', OUT/'protocol.json',
             ROOT/'data/external/latest_state_energy_GWh.csv']})
    (OUT/'run.json').write_text(json.dumps(info, indent=2)+'\n')
    print(json.dumps(info, indent=2))


if __name__ == '__main__':
    main()
