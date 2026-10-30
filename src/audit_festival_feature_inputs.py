"""Reconstruct persisted foundation input bytes without feature/model helpers."""
from datetime import timedelta
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT/'results/festival_features_v1'
FAMILIES = ['Holi', 'Dussehra', 'Ganesh_Chaturthi', 'Ugadi_Gudi_Padwa', 'Diwali']


def sha(a):
    return hashlib.sha256(a.tobytes()).hexdigest()


def main(out, models):
    data = pd.read_csv(ROOT/'data/external/latest_state_energy_GWh.csv', index_col=0, parse_dates=True).asfreq('D')
    filled = {}
    for state in ['Delhi', 'Karnataka', 'Maharashtra']:
        values = data[state].to_numpy(dtype=float, copy=True)
        for i in range(len(values)):
            if not np.isfinite(values[i]) or values[i] <= 0:
                values[i] = values[i-7] if i >= 7 and np.isfinite(values[i-7]) else values[i-1] if i > 0 else np.nan
        filled[state] = pd.Series(values, index=data.index)
    true = pd.read_csv(PARENT/'anchors_2022_2025.csv', parse_dates=['date'])
    fake = pd.read_csv(PARENT/'placebo_anchors.csv', parse_dates=['date'])
    references = pd.read_csv(out/'primary_cases.csv')
    expected_tasks = set(map(tuple, references[['state', 'origin']].drop_duplicates().to_numpy()))
    checks, quantile_issues = {}, []
    for model in models:
        run = json.loads((out/model/'run.json').read_text())
        inputs = json.loads((out/model/'inputs.json').read_text())
        protocol = json.loads((out/'protocol.json').read_text())
        assert len(inputs) == len(expected_tasks)*len(protocol['arms'])
        for arm in protocol['arms']:
            records = [r for r in inputs if r['arm'] == arm]
            assert {(r['state'], r['origin']) for r in records} == expected_tasks
            for r in records:
                origin = pd.Timestamp(r['origin'])
                dates = pd.date_range(origin-pd.Timedelta(days=730), periods=744)
                assert dates.min() >= pd.Timestamp('2022-01-01') and dates.max() <= pd.Timestamp('2025-12-31')
                target = filled[r['state']].reindex(dates[:730]).to_numpy(dtype=np.float32)
                columns = [(dates.dayofweek == k).astype(float) for k in range(7)]
                for k in [1, 2, 3]:
                    columns.extend([np.sin(2*np.pi*k*dates.dayofyear/365.2425), np.cos(2*np.pi*k*dates.dayofyear/365.2425)])
                if arm == 'zero5':
                    columns.extend([np.zeros(len(dates)) for _ in FAMILIES])
                elif arm != 'calendar':
                    ledger = fake if arm.startswith('placebo') else true
                    for family in FAMILIES:
                        anchors = ledger[ledger.state.eq(r['state']) & ledger.family.eq(family)].date
                        targets = list(anchors)
                        if 'window' in arm:
                            targets = [d for a in anchors for d in pd.date_range(a-pd.Timedelta(days=3), a+pd.Timedelta(days=3))]
                        columns.append(dates.isin(targets).astype(float))
                cov = np.asarray(columns, dtype=np.float32)
                assert sha(target) == r['target_sha256'], (model, arm, r['origin'], 'target')
                assert sha(cov) == r['covariate_sha256'], (model, arm, r['origin'], 'covariates')
                assert r['feature_count'] == len(columns)
                assert r['future_target_perturbation_invariant']
                assert pd.Timestamp(r['context_end']) == origin-pd.Timedelta(days=1)
                assert np.count_nonzero(cov[13:, :730], axis=1).astype(int).tolist() == r['past_nonzero_counts']
        solo = json.loads((out/model/'solo_batch_audit.json').read_text())
        assert len(solo) == 4*len(protocol['arms'])
        d = pd.read_csv(out/model/'predictions.csv')
        qcols = sorted(c for c in d if c.startswith('q_'))
        q = d[qcols].to_numpy()
        assert np.isfinite(q).all()
        bad = np.diff(q, axis=1) < 0
        assert int(bad.sum()) == run['native_quantile_crossings']
        for i, j in zip(*np.where(bad)):
            r = d.iloc[i]
            quantile_issues.append(dict(model=model, arm=r.arm, family=r.family, state=r.state,
                origin=r.origin, date=r.date, horizon=int(r.horizon), lower_level=qcols[j], upper_level=qcols[j+1],
                lower_prediction=float(q[i, j]), upper_prediction=float(q[i, j+1])))
        checks[model] = dict(reconstructed_input_tasks=len(inputs), native_quantile_crossings=int(bad.sum()),
            max_first_batch_solo_difference=max(r['max_abs_difference'] for r in solo),
            weight_sha256=run['weight_sha256'])
    suffix = '' if len(models) == 2 else '_'+models[0]
    pd.DataFrame(quantile_issues, columns=['model', 'arm', 'family', 'state', 'origin', 'date', 'horizon',
        'lower_level', 'upper_level', 'lower_prediction', 'upper_prediction']).to_csv(out/f'native_quantile_crossings{suffix}.csv', index=False)
    result = dict(status='pass', scope='Separate date/NumPy reconstruction of actual target/covariate bytes; not external human review or training-corpus/real-time clearance',
        models=checks, quantile_treatment='All native outputs retained unchanged; no sorting/clipping')
    (out/f'input_audit{suffix}.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--out', type=Path, default=PARENT)
    p.add_argument('--model', choices=['chronos', 'timesfm'])
    args = p.parse_args()
    main(args.out.resolve(), [args.model] if args.model else ['chronos', 'timesfm'])
