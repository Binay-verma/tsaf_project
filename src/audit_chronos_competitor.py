"""Separate raw/scalar input and chronology audit; no future actuals opened."""
from datetime import datetime, date, timezone
import hashlib
import json
from pathlib import Path
from statistics import mean
import subprocess
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'results/prospective_chronos_20261031_v1'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    if (OUT/'independent_audit.json').exists():
        raise FileExistsError('Preserve prior future input audit')
    protocol = json.loads((OUT/'protocol.json').read_text())
    for name, expected in protocol['source_hashes'].items():
        assert sha(ROOT/name) == expected, name
    freeze = json.loads((OUT/'freeze.json').read_text())
    assert sha(OUT/'protocol.json') == freeze['protocol_sha256']
    assert sha(OUT/'predictions.csv') == freeze['predictions_sha256']
    assert sha(OUT/'inputs.json') == freeze['inputs_sha256']
    issued = datetime.fromisoformat(freeze['issued_utc'])
    started = datetime.fromisoformat(freeze['started_utc'])
    india = ZoneInfo('Asia/Calcutta')
    assert issued.tzinfo is not None and started <= issued
    assert issued.astimezone(india).date() == date(2026, 10, 31)
    assert issued < datetime(2026, 11, 1, tzinfo=india)
    source = pd.read_csv(ROOT/protocol['context_snapshot'], index_col=0, parse_dates=True).asfreq('D')
    assert source.index.max() == pd.Timestamp('2026-10-28')
    origin = pd.Timestamp('2026-10-29')
    dates = pd.date_range(origin-pd.Timedelta(days=730), periods=744)
    columns = [(dates.dayofweek == j).astype(float) for j in range(7)]
    for harmonic in [1, 2, 3]:
        columns += [np.sin(2*np.pi*harmonic*dates.dayofyear/365.2425),
                    np.cos(2*np.pi*harmonic*dates.dayofyear/365.2425)]
    covariates = np.asarray(columns, dtype=np.float32)
    input_log = json.loads((OUT/'inputs.json').read_text())
    assert len(input_log) == 6
    scales = {}
    for state in protocol['states']:
        a = source[state].to_numpy(dtype=float, copy=True)
        for i, value in enumerate(a):
            if not np.isfinite(value):
                a[i] = a[i-7] if i >= 7 and np.isfinite(a[i-7]) else a[i-1] if i else np.nan
        target = pd.Series(a, index=source.index).reindex(dates[:730]).to_numpy(dtype=np.float32)
        assert len(target) == 730 and np.isfinite(target).all()
        y = source[state].loc['2024-01-02':'2025-12-31'].to_dict()
        scales[state] = mean(abs(value-y[day-pd.Timedelta(days=7)]) for day, value in y.items()
            if day-pd.Timedelta(days=7) in y and np.isfinite(value) and np.isfinite(y[day-pd.Timedelta(days=7)]))
        for mode in ['history', 'calendar']:
            record = [r for r in input_log if r['state'] == state and r['mode'] == mode]
            assert len(record) == 1
            record = record[0]
            assert record['target_sha256'] == hashlib.sha256(target.tobytes()).hexdigest()
            assert record['covariate_sha256'] == (None if mode == 'history' else hashlib.sha256(covariates.tobytes()).hexdigest())
            assert record['feature_count'] == (0 if mode == 'history' else 13)
            names = [f'dow_{i}' for i in range(7)]+[f'{wave}_{k}' for k in [1, 2, 3] for wave in ['sin', 'cos']]
            assert record['feature_names'] == ([] if mode == 'history' else names)
            assert record['future_target_perturbation_invariant']
            assert record['context_end'] == '2026-10-28'
    predictions = pd.read_csv(OUT/'predictions.csv')
    assert len(predictions) == 84 and predictions.prospective_eligible.sum() == 66
    assert set(predictions.model) == {'chronos2_history', 'chronos2_calendar'}
    assert not predictions.duplicated(['state', 'model', 'horizon']).any()
    quantiles = freeze['all_quantiles']
    qcols = [f'q_{int(round(q*1000)):03d}' for q in quantiles]
    assert len(quantiles) == len(qcols) == 21
    assert np.isfinite(predictions[qcols+['prediction', 'mase_scale']]).all().all()
    assert np.array_equal(predictions.prediction.to_numpy(), predictions.q_500.to_numpy())
    for row in predictions.itertuples():
        day = date.fromisoformat(row.date)
        assert day-origin.date() == pd.Timedelta(days=row.horizon-1)
        assert row.origin == '2026-10-29' and row.issued_utc == freeze['issued_utc']
        assert abs(row.mase_scale-scales[row.state]) < 1e-10
        expected = date(2026, 11, 1) <= day <= date(2026, 11, 11)
        assert row.prospective_eligible == expected
        if expected:
            assert datetime.combine(day, datetime.min.time(), tzinfo=india) > issued
    assert int((np.diff(predictions[qcols].to_numpy(), axis=1) < 0).sum()) == freeze['native_crossing_pairs']
    solo = json.loads((OUT/'solo_batch_audit.json').read_text())
    assert len(solo) == 6 and all(np.isfinite(r['maximum_absolute_difference_GWh']) for r in solo)
    # Point/native source identity, without interpreting future distributions as results.
    weight = json.loads((ROOT/'results/mechanism_controls_v1/chronos_download.json').read_text())
    expected = next(r for r in weight['files'] if r['name'] == 'model.safetensors')['sha256']
    assert freeze['weight_sha256'] == expected == 'ddcda3c7508bf2528087723e98a20707cc04b7f370ae275a9fd88078ddba4f42'
    for name in ['protocol.json', 'predictions.csv', 'freeze.json']:
        relative = 'results/prospective_20261030_v1/'+name
        original = subprocess.check_output(['git', 'show', 'cabd5982e1948652b9841d6c31a2380f6f314198:'+relative], cwd=ROOT)
        assert original == (ROOT/relative).read_bytes()
    audit = dict(status='pass', audited_utc=datetime.now(timezone.utc).isoformat(),
        scope='Separate NumPy/scalar past-input/calendar/scales/fullIndia-day/native/parent-preservation audit; no future actuals or independent human review.',
        reconstructed_input_tasks=6, rows=84, eligible_rows=66,
        recorded_issued_utc=freeze['issued_utc'], eligible_start='2026-11-01',
        predictions_sha256=freeze['predictions_sha256'], native_crossing_pairs=freeze['native_crossing_pairs'],
        public_freeze_status='Normal public push/observed receipt before eligible day still required',
        future_accuracy_available=False)
    (OUT/'independent_audit.json').write_text(json.dumps(audit, indent=2)+'\n')
    print(json.dumps(audit, indent=2))


if __name__ == '__main__':
    main()
