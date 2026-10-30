"""Manual later comparison on the ORIGINAL episode's exact actual vintage.

Never fetches data, activates a workflow, overwrites a forecast or scores early.
"""
import argparse
from datetime import datetime, date, timezone
import hashlib
import json
from pathlib import Path
import subprocess
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from forecasting import ROOT
from collect_prospective_actuals import complete_result

ANNEX = ROOT/'results/prospective_chronos_20261031_v1'
PARENT = ROOT/'results/prospective_20261030_v1'
ACTUALS = ROOT/'results/prospective_20261030_scoring_v1'
FIRST = date(2026, 11, 1)
LAST = date(2026, 11, 11)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def point_cases(parent, new, actuals, now):
    if now.tzinfo is None or now.astimezone(timezone.utc).date() <= LAST:
        raise ValueError('No score before the complete future period endsUTC')
    if actuals.index.has_duplicates:
        raise ValueError('Duplicate actual dates')
    chunks = []
    for frame in [parent, new]:
        frame = frame.copy()
        frame['day'] = pd.to_datetime(frame.date)
        frame = frame[frame.day.between(pd.Timestamp(FIRST), pd.Timestamp(LAST))]
        if frame.duplicated(['state', 'model', 'day']).any():
            raise ValueError('Duplicate prediction identity')
        chunks.append(frame)
    d = pd.concat(chunks, ignore_index=True)
    if len(d) != 264 or d.model.nunique() != 8:
        raise ValueError('Require all8fixedconfigurations/264matchedcaseforecasts')
    expected = {(state, day) for state in ['Delhi', 'Karnataka', 'Maharashtra']
                for day in pd.date_range(FIRST, LAST)}
    for model, group in d.groupby('model'):
        if set(zip(group.state, group.day)) != expected:
            raise ValueError('Mismatched dates/states for '+model)
    d['actual'] = [actuals.at[row.day, row.state] if row.day in actuals.index and row.state in actuals else np.nan for row in d.itertuples()]
    if not np.isfinite(d[['actual', 'prediction', 'mase_scale']]).all().all() or not d.actual.gt(0).all() or not d.mase_scale.gt(0).all():
        raise ValueError('Missing/nonpositiveactuals/scales; neverimpute/drop')
    d['MAE_GWh'] = abs(d.prediction-d.actual)
    d['MASE'] = d.MAE_GWh/d.mase_scale
    return d


def first_commit_guard():
    relative = str((ANNEX/'predictions.csv').relative_to(ROOT))
    commits = subprocess.check_output(['git', 'rev-list', '--reverse', 'HEAD', '--', relative], cwd=ROOT, text=True).splitlines()
    if not commits:
        raise ValueError('Require a public pre-outcome forecast commit')
    first = commits[0]
    for name in ['protocol.json', 'predictions.csv', 'freeze.json', 'inputs.json', 'solo_batch_audit.json', 'independent_audit.json']:
        name = str((ANNEX/name).relative_to(ROOT))
        original = subprocess.check_output(['git', 'show', first+':'+name], cwd=ROOT)
        if original != (ROOT/name).read_bytes():
            raise ValueError('Frozen first-commit artifact changed:'+name)
    timestamp = subprocess.check_output(['git', 'show', '-s', '--format=%cI', first], cwd=ROOT, text=True).strip()
    commit_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    freeze = json.loads((ANNEX/'freeze.json').read_text())
    issued = datetime.fromisoformat(freeze['issued_utc'])
    start = datetime(2026, 11, 1, tzinfo=ZoneInfo('Asia/Calcutta'))
    if not issued <= commit_time < start:
        raise ValueError('Invalid completion/commit/fullIndia-day chronology')
    receipt = json.loads((ANNEX/'public_receipt.json').read_text())
    observed = datetime.fromisoformat(receipt['observed_utc'])
    if receipt['first_forecast_commit'] != first or not commit_time <= observed < start or receipt['predictions_sha256'] != sha(ANNEX/'predictions.csv'):
        raise ValueError('Require observed normal remote receipt before eligible day')
    return first


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, default=ROOT/'results/prospective_chronos_20261031_scoring_v1')
    args = parser.parse_args()
    now = datetime.now(timezone.utc)
    if now.date() <= LAST:
        print('PENDING: no labels opened or network request; score onlyafter11NovemberendsUTC using original actual vintage.')
        return
    if args.out.exists():
        raise FileExistsError('Preserve first evaluation')
    protocol = json.loads((ANNEX/'protocol.json').read_text())
    for name, expected in protocol['source_hashes'].items():
        assert sha(ROOT/name) == expected, name
    first = first_commit_guard()
    if not complete_result(ACTUALS):
        raise ValueError('Original episode first actual receipt is incomplete; no alternative retrieval')
    receipt = json.loads((ACTUALS/'collection.json').read_text())
    retrieved = datetime.fromisoformat(receipt['retrieved_utc'].replace('Z', '+00:00'))
    assert retrieved.tzinfo is not None and retrieved <= now and retrieved.astimezone(timezone.utc).date() > LAST
    actuals = pd.read_csv(ACTUALS/'actuals_snapshot.csv', index_col=0, parse_dates=True)
    assert sha(ACTUALS/'actuals_snapshot.csv') == receipt['eligible_labels_sha256']
    metadata = json.loads((ACTUALS/'source_metadata_snapshot.json').read_text())
    fields = {row['name']: row for row in metadata['fields']}
    assert all(fields[state+': EnergyMet']['units'] == 'GWh' for state in ['Delhi', 'Karnataka', 'Maharashtra'])
    parent = pd.read_csv(PARENT/'predictions.csv')
    new = pd.read_csv(ANNEX/'predictions.csv')
    d = point_cases(parent, new, actuals, now)
    state = d.groupby(['model', 'state'])[['MAE_GWh', 'MASE']].mean().reset_index()
    macro = state.groupby('model')[['MAE_GWh', 'MASE']].mean().reset_index()
    steps = d.groupby(['model', 'horizon'])[['MAE_GWh', 'MASE']].mean().reset_index()
    q = d[d.model.isin(['chronos2_history', 'chronos2_calendar', 'timesfm3_history', 'timesfm3_calendar'])].copy()
    assert len(q) == 132
    for k in range(1, 10):
        q.loc[q.model.str.startswith('timesfm3_'), f'q_{100*k:03d}'] = q.loc[q.model.str.startswith('timesfm3_'), f'q{k:02d}']
    values = q[[f'q_{100*k:03d}' for k in range(1, 10)]].to_numpy()
    assert np.isfinite(values).all()
    y, scale = q.actual.to_numpy(), q.mase_scale.to_numpy()
    lo, median, hi = values[:, 0], values[:, 4], values[:, 8]
    invalid = lo > hi
    tau = np.arange(1, 10)/10
    residual = y[:, None]-values
    q['scaled_mean_pinball'] = np.maximum(tau*residual, (tau-1)*residual).mean(axis=1)/scale
    q['invalid80'] = invalid
    q['common_crossings'] = (np.diff(values, axis=1) < 0).sum(axis=1)
    q['coverage80'] = np.where(invalid, np.nan, ((lo <= y)&(y <= hi)).astype(float))
    q['scaled_width80'] = np.where(invalid, np.nan, hi-lo)/scale
    q['scaled_WIS80_median'] = np.where(invalid, np.nan,
        (.5*abs(y-median)+.1*(hi-lo+10*np.maximum(lo-y, 0)+10*np.maximum(y-hi, 0)))/1.5)/scale
    fields = ['scaled_mean_pinball', 'coverage80', 'scaled_width80', 'scaled_WIS80_median']
    qs = q.groupby(['model', 'state'])[fields].mean().reset_index()
    qm = qs.groupby('model')[fields].mean().reset_index()
    for model, bad in q.groupby('model').invalid80.any().items():
        if bad:
            qm.loc[qm.model.eq(model), fields[1:]] = np.nan
    args.out.mkdir(parents=True)
    d.to_csv(args.out/'scored_cases.csv', index=False)
    state.to_csv(args.out/'metrics_state.csv', index=False)
    macro.to_csv(args.out/'metrics_macro.csv', index=False)
    steps.to_csv(args.out/'metrics_model_step.csv', index=False)
    q.to_csv(args.out/'native_cases.csv', index=False)
    qm.to_csv(args.out/'native_metrics_macro.csv', index=False)
    audit = dict(scored_utc=now.isoformat(), first_forecast_commit=first,
        actual_vintage_sha256=receipt['eligible_labels_sha256'], actuals_retrieved_utc=retrieved.isoformat(),
        point_rows=264, native_rows=132, models=8, model_steps=list(range(4, 15)),
        same_vintage_as_original=True, future_arm_selection=False,
        limits='Sameepisode/source/stalecontext withdifferentactualissuances; date/modelstepconfounded. No independentyear/source, festivalfeatureconfirmation, rowindependenttests or guaranteedcoverage.')
    (args.out/'audit.json').write_text(json.dumps(audit, indent=2)+'\n')
    print(macro.to_string(index=False))


if __name__ == '__main__':
    main()
