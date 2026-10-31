"""Separate CSV/scalar audit for later rolling scores; never fetches data."""
import argparse
import csv
from datetime import datetime, timezone, date, timedelta
import gzip
import io
import json
import math
import subprocess
from pathlib import Path
from statistics import mean
from collections import defaultdict

from rolling_evidence_v1 import ROOT, BASE, STATES, FAMILIES, collection_gate, first_commit_guard, sha, dump, planned, INDIA
from rolling_confirmation_plan import MODELS, ARMS, LEADS
from rolling_execution_v1 import verify_actuals


def read(path):
    with Path(path).open(newline='') as stream:
        return list(csv.DictReader(stream))


def key(row):
    return row['model'], row['arm'], row['state'], int(row['decision_lead'])


def close(expected, value):
    if math.isnan(expected):
        if value not in ['', None] and not math.isnan(float(value)):
            raise ValueError('Undefined interval was silently dropped/repaired')
    elif value in ['', None] or not math.isclose(expected, float(value), rel_tol=1e-10, abs_tol=1e-10):
        raise ValueError(('Scalar score mismatch', expected, value))


def audit(folder, now=None):
    folder = Path(folder)
    freeze = json.loads((folder/'freeze.json').read_text())
    collection_gate(freeze['number'], now or datetime.now(timezone.utc))
    first = first_commit_guard(folder)
    actual_meta = verify_actuals(folder)
    actuals = read(folder/'actuals/actuals.csv')
    values = {(row['date'], state): float(row[state]) for row in actuals for state in STATES}
    if len(values) != len(actuals)*3 or any(not math.isfinite(v) or v <= 0 for v in values.values()):
        raise ValueError('Duplicated or unrecorded actual labels')
    raw = (folder/'actuals/source.raw').read_bytes()
    metadata = (folder/'actuals/metadata.raw').read_bytes()
    decoded = lambda b: gzip.decompress(b) if b[:2] == b'\x1f\x8b' else b
    fields = {row['name']: row for row in json.loads(decoded(metadata))['fields']}
    if any(fields[state+': EnergyMet']['units'] != 'GWh' for state in STATES):
        raise ValueError('Source unit changed')
    source_values = {}
    for row in csv.DictReader(io.StringIO(decoded(raw).decode())):
        d = datetime.strptime(row['yyyymmdd'], '%Y%m%d').date().isoformat()
        for state in STATES:
            if (d, state) in values:
                if (d, state) in source_values:
                    raise ValueError('Duplicate target source dates')
                source_values[d, state] = float(row[state+': EnergyMet'])
    if source_values.keys() != values.keys():
        raise ValueError('Selected actual date set differs from raw first vintage')
    for k, v in values.items():
        close(v, source_values[k])
    predictions = read(folder/'predictions.csv')
    scored = read(folder/'scores/cases.csv')
    if len(predictions) != 432 or len(scored) != 432 or len({key(r) for r in scored}) != 432:
        raise ValueError('Incomplete/duplicated scored matrix')
    expected_keys = {(m, a, s, k) for m in MODELS for a in ARMS for s in STATES for k in LEADS}
    if {key(row) for row in predictions} != expected_keys or {key(row) for row in scored} != expected_keys:
        raise ValueError('Fixed configuration matrix changed')
    scored = {key(row): row for row in scored}
    native = {(r['model'], r['arm'], r['state'], int(r['model_step'])): r for r in read(folder/'native_paths.csv')}
    if len(native) != 768:
        raise ValueError('Incomplete native paths')
    recomputed = []
    decision = planned(freeze['number']).astimezone(INDIA).date()
    for row in predictions:
        out = scored[key(row)]
        if row['date'] != (decision+timedelta(days=int(row['decision_lead']))).isoformat() or row['model_origin'] != (decision-timedelta(days=1)).isoformat() or row['context_last_date'] != (decision-timedelta(days=2)).isoformat() or int(row['model_step']) != int(row['decision_lead'])+2:
            raise ValueError('D-2 availability/decision/model date geometry changed')
        for name in ['model_origin', 'context_last_date', 'date', 'model_step', 'event_families']:
            if row[name] != out[name]:
                raise ValueError('Case identity/subgroup changed')
        value = values[row['date'], row['state']]
        scale, point = float(row['mase_scale']), float(row['prediction'])
        expected = {'actual': value, 'prediction': point, 'mase_scale': scale,
                    'MAE_GWh': abs(value-point), 'MASE': abs(value-point)/scale}
        if row['model'] in ['chronos', 'timesfm']:
            path = native[row['model'], row['arm'], row['state'], int(row['model_step'])]
            close(point, path['prediction'])
            q = [float(row[f'q_{k*100:03d}']) for k in range(1, 10)]
            for k, v in enumerate(q, 1):
                close(v, path[f'q_{k*100:03d}'])
                close(v, out[f'q_{k*100:03d}'])
            losses = []
            for k, v in enumerate(q, 1):
                residual, alpha = value-v, k/10
                losses.append(alpha*residual if residual >= 0 else (alpha-1)*residual)
            lo, med, hi = q[0], q[4], q[8]
            expected['scaled_pinball'] = mean(losses)/scale
            expected['native_common_crossing_pairs'] = sum(b < a for a, b in zip(q, q[1:]))
            if lo > hi:
                expected.update(coverage80=math.nan, scaled_width80=math.nan, scaled_WIS80_median=math.nan)
            else:
                interval_score = hi-lo
                if value < lo:
                    interval_score += 10*(lo-value)
                if value > hi:
                    interval_score += 10*(value-hi)
                expected.update(coverage80=float(lo <= value <= hi), scaled_width80=(hi-lo)/scale,
                    scaled_WIS80_median=(.5*abs(value-med)+.1*interval_score)/1.5/scale)
        for name, value in expected.items():
            close(value, out[name])
        recomputed.append((row, expected))
    groups = defaultdict(lambda: defaultdict(list))
    for row, values in recomputed:
        families = row['event_families'].split('|') if row['event_families'] else []
        scopes = ['all']+(families if families else ['outside_named_windows'])
        for scope in scopes:
            group = row['model'], row['arm'], int(row['decision_lead']), scope
            groups[group][row['state']].append(values)
    reported = read(folder/'scores/metrics.csv')
    if len(reported) != len(groups) or len({(r['model'], r['arm'], int(r['decision_lead']), r['scope']) for r in reported}) != len(groups):
        raise ValueError('Aggregate case groups missing/duplicated')
    checked = 0
    for row in reported:
        block = groups[row['model'], row['arm'], int(row['decision_lead']), row['scope']]
        close(len(block), row['states'])
        close(sum(len(v) for v in block.values()), row['cases'])
        for field in ['MAE_GWh', 'MASE', 'scaled_pinball', 'coverage80', 'scaled_width80', 'scaled_WIS80_median']:
            available = [r[field] for records in block.values() for r in records if field in r]
            if available:
                value = math.nan if any(math.isnan(v) for v in available) else mean(mean(r[field] for r in records) for records in block.values())
                close(value, row[field])
                checked += 1
            elif row.get(field, ''):
                raise ValueError('Probability metric attached to a local point-only model')
    return dict(status='pass', audited_utc=datetime.now(timezone.utc).isoformat(),
        scope='Internal separate standard-library raw-source/point/native/scalar/equal-state aggregate audit; not independent human/model reimplementation.',
        scored_cases=432, aggregate_fields=checked, native_paths=768,
        first_forecast_commit=first, first_actuals_sha256=actual_meta['actuals_sha256'],
        cases_sha256=sha(folder/'scores/cases.csv'), metrics_sha256=sha(folder/'scores/metrics.csv'),
        audit_source_sha256=sha(__file__))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--number', required=True, type=int)
    args = parser.parse_args()
    collection_gate(args.number, datetime.now(timezone.utc))
    folder = BASE/'issuances'/f'{args.number:02d}'
    registration = BASE/'scalar_audit_registration_v1.json'
    relative = str(registration.relative_to(ROOT))
    first = subprocess.check_output(['git', 'rev-list', '--reverse', 'HEAD', '--', relative], cwd=ROOT, text=True).splitlines()[0]
    record = json.loads(registration.read_text())
    for name in [relative]+list(record['sources']):
        original = subprocess.check_output(['git', 'show', first+':'+name], cwd=ROOT)
        if original != (ROOT/name).read_bytes():
            raise ValueError('Audit source/registration changed from first commit:'+name)
        if name != relative and sha(ROOT/name) != record['sources'][name]:
            raise ValueError('Registered audit source hash mismatch')
    recorded = datetime.fromisoformat(subprocess.check_output(['git', 'show', '-s', '--format=%cI', first], cwd=ROOT, text=True).strip())
    issued = datetime.fromisoformat(json.loads((folder/'freeze.json').read_text())['issued_utc'])
    if recorded > issued:
        raise ValueError('Scalar audit must be publicly registered before issuance')
    destination = folder/'scores/independent_scalar_audit.json'
    if destination.exists():
        raise FileExistsError('Preserve prior audit')
    result = audit(folder)
    dump(destination, result)
    print('PASS:', result['scored_cases'], 'scored cases, scalar audit')
