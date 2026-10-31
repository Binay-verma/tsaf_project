"""Evidence contracts for the unactivated manual rolling study.

No network, automatic scheduler, clock override CLI, or old-freeze writes.
"""
from datetime import datetime, timedelta, timezone
import gzip
import hashlib
import io
import json
from pathlib import Path
import subprocess
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from rolling_confirmation_plan import STATES, MODELS, ARMS, LEADS, schedule, target_contract

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'results/rolling_confirmation_runtime_v1'
SOURCE = 'https://robbieandrew.github.io/india/data/POSOCO_data.csv'
METADATA = 'https://robbieandrew.github.io/india/data/POSOCO_metadata.json'
FAMILIES = ['Holi', 'Dussehra', 'Ganesh_Chaturthi', 'Ugadi_Gudi_Padwa', 'Diwali']
INDIA = ZoneInfo('Asia/Kolkata')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


def within(parent, relative):
    parent = Path(parent).resolve()
    path = (parent/relative).resolve()
    if Path(relative).is_absolute() or not path.is_relative_to(parent):
        raise ValueError('Evidence path escapes its package')
    return path


def aware(now):
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError('Explicit timezone required')
    return now.astimezone(timezone.utc)


def planned(number):
    if not 0 <= number < 52:
        raise ValueError('Issuance number must be0..51')
    return schedule()[number]


def issuance_gate(number, now):
    now = aware(now)
    start = planned(number)
    if not start <= now <= start+timedelta(minutes=59):
        raise ValueError('Outside scheduled issuance window; never backdate or reschedule')
    return target_contract(start)


def collection_gate(number, now):
    now = aware(now)
    last = datetime.fromisoformat(target_contract(planned(number))['targets']['14'])
    if now < (last+timedelta(days=1)).replace(tzinfo=timezone.utc):
        raise ValueError('No actual-source access before full target period ends UTC')


def parse_source(raw, metadata_raw):
    def decoded(value):
        return gzip.decompress(value) if value[:2] == b'\x1f\x8b' else value
    meta = json.loads(decoded(metadata_raw))
    fields = {field['name']: field for field in meta['fields']}
    for state in STATES:
        if fields[state+': EnergyMet']['units'] != 'GWh':
            raise ValueError('Unexpected supplied-energy units')
    frame = pd.read_csv(io.BytesIO(decoded(raw)))
    dates = pd.to_datetime(frame.yyyymmdd.astype(str), format='%Y%m%d', errors='raise')
    if dates.duplicated().any():
        raise ValueError('Duplicate source dates')
    selected = frame[[state+': EnergyMet' for state in STATES]].apply(pd.to_numeric, errors='raise')
    selected.columns = STATES
    selected.index = pd.DatetimeIndex(dates)
    selected = selected.sort_index().asfreq('D')
    selected.index.name = 'date'
    # Nonpositive and nonfinite records are unavailable labels, never score imputations.
    return selected.where(np.isfinite(selected)&selected.gt(0))


def available_history(source, number):
    contract = target_contract(planned(number))
    cutoff = pd.Timestamp(contract['context_last_date'])
    history = source.loc[:cutoff].copy()
    if history.empty or history.index.min() > cutoff-pd.Timedelta(days=1095):
        raise ValueError('Insufficient older history for730dayfit plus annual lags')
    if history.index.max() < cutoff:
        raise ValueError('D-2 source endpoint absent; no silent origin shift')
    history = history.asfreq('D')
    return history.where(np.isfinite(history)&history.gt(0))


def frozen_scales(history, number):
    # Clarifies the plan's pre-year rule before any new outcomes: issuance year,
    # including forecasts that cross New Year. Never future target-year labels.
    end = pd.Timestamp(f'{planned(number).year-1}-12-31')
    result = {}
    for state in STATES:
        values = history[state].reindex(pd.date_range(end-pd.Timedelta(days=729), end))
        differences = (values-values.shift(7)).abs().dropna()
        if len(differences) < 365 or not np.isfinite(differences.mean()) or differences.mean() <= 0:
            raise ValueError('Insufficient fixed pre-issuance-year weekly scale')
        result[state] = float(differences.mean())
    return result


def calendar_package(manifest_path, number, now):
    """Validate explicit documents/coverage/anchors; never guess a holiday date."""
    now = aware(now)
    manifest_path = Path(manifest_path)
    manifest = json.loads(manifest_path.read_text())
    parent = manifest_path.parent
    context = target_contract(planned(number))
    first = pd.Timestamp(context['model_origin'])-pd.Timedelta(days=730)
    last = pd.Timestamp(context['targets']['14'])
    years = set(range((first-pd.Timedelta(days=3)).year, (last+pd.Timedelta(days=3)).year+1))
    coverage = manifest['coverage']
    wanted = {(state, year, family) for state in STATES for year in years for family in FAMILIES}
    given = {(row['state'], row['year'], row['family']) for row in coverage}
    if not given.issuperset(wanted) or len(coverage) != len(given):
        raise ValueError('Incomplete/duplicate state/year/family coverage')
    documents = manifest['documents']
    for key, doc in documents.items():
        if not doc.get('primary_document_url') or not doc.get('date_definition'):
            raise ValueError('Missing primary calendar provenance/definition')
        if aware(datetime.fromisoformat(doc['notice_utc'])) > now:
            raise ValueError('Calendar notice not yet available')
        file = within(parent, doc['file'])
        if not file.read_bytes().startswith(b'%PDF-') or sha(file) != doc['sha256']:
            raise ValueError('Calendar document changed:'+key)
    anchor_path, fake_path = within(parent, manifest['anchors']), within(parent, manifest['placebos'])
    anchors = pd.read_csv(anchor_path, keep_default_na=False)
    fake = pd.read_csv(fake_path, keep_default_na=False)
    if sha(anchor_path) != manifest['anchors_sha256'] or sha(fake_path) != manifest['placebos_sha256']:
        raise ValueError('Calendar ledger hash mismatch')
    keys = ['state', 'year', 'family', 'date']
    if anchors.duplicated(keys).any() or fake.duplicated(keys).any():
        raise ValueError('Duplicate named/placebo anchors')
    for row in coverage:
        if row['document'] not in documents or row['status'] not in ['named_dates', 'not_in_state_scope']:
            raise ValueError('Undocumented or unspecified family scope')
        doc = documents[row['document']]
        if doc['state'] != row['state'] or doc['year'] != row['year']:
            raise ValueError('Wrong state/year calendar evidence')
        matches = anchors[(anchors.state == row['state'])&(anchors.year == row['year'])&(anchors.family == row['family'])]
        if (row['status'] == 'named_dates') != (len(matches) > 0):
            raise ValueError('Missing dates or contradictory absent-family declaration')
    for row in anchors.to_dict('records'):
        if (row['state'], row['year'], row['family']) not in given or pd.Timestamp(row['date']).year != row['year'] or row['document'] not in documents:
            raise ValueError('Anchor outside documented coverage')
        matching = [r for r in coverage if (r['state'], r['year'], r['family']) == (row['state'], row['year'], row['family'])]
        if row['document'] != matching[0]['document']:
            raise ValueError('Anchor document differs from coverage declaration')
    true_keys = set(map(tuple, anchors[keys].to_numpy()))
    fake_parent = {(row['state'], row['year'], row['family'], row['original_date']) for row in fake.to_dict('records')}
    if fake_parent != true_keys or len(fake) != len(anchors):
        raise ValueError('Placebos must preserve every registered named/subsidiary anchor')
    for row in fake.to_dict('records'):
        actual, placebo = pd.Timestamp(row['original_date']), pd.Timestamp(row['date'])
        shift = (placebo-actual).days
        if abs(shift) not in [28, 35, 42] or shift != int(row['shift_days']) or placebo.year != row['year']:
            raise ValueError('Invalid fixed weekday placebo shift')
        same = pd.to_datetime(anchors[anchors.state.eq(row['state'])].date)
        if any(abs((placebo-day).days) <= 6 for day in same):
            raise ValueError('Placebo and named windows overlap')
    return manifest, anchors, fake


def covariates(index, state, arm, anchors, fake):
    if arm not in ARMS:
        raise ValueError(arm)
    base = pd.DataFrame({f'dow_{k}': (index.dayofweek == k).astype(float) for k in range(7)}, index=index)
    for k in [1, 2, 3]:
        base[f'sin_{k}'] = np.sin(2*np.pi*k*index.dayofyear/365.2425)
        base[f'cos_{k}'] = np.cos(2*np.pi*k*index.dayofyear/365.2425)
    if arm == 'calendar':
        return base
    ledger = fake if arm.startswith('placebo_') else anchors
    extras = np.zeros((len(index), 5), dtype=float)
    if arm != 'zero5':
        for k, family in enumerate(FAMILIES):
            dates = pd.to_datetime(ledger[ledger.state.eq(state)&ledger.family.eq(family)].date)
            if 'window' in arm:
                dates = [day for anchor in dates for day in pd.date_range(anchor-pd.Timedelta(days=3), anchor+pd.Timedelta(days=3))]
            extras[:, k] = index.isin(dates).astype(float)
        if arm.startswith('pooled_'):
            extras[:, 0] = extras.any(axis=1)
            extras[:, 1:] = 0
    return pd.concat([base, pd.DataFrame(extras, index=index, columns=[f'event_{k}' for k in range(5)])], axis=1)


def case_matrix(rows, number):
    expected = {(m, a, s, k) for m in MODELS for a in ARMS for s in STATES for k in LEADS}
    got = {(r['model'], r['arm'], r['state'], int(r['decision_lead'])) for r in rows}
    if got != expected or len(rows) != len(expected):
        raise ValueError('Incomplete/duplicate fixed432forecast matrix')
    contract = target_contract(planned(number))
    for row in rows:
        lead = int(row['decision_lead'])
        if row['date'] != contract['targets'][str(lead)] or int(row['model_step']) != lead+2 or row['context_last_date'] != contract['context_last_date'] or row['model_origin'] != contract['model_origin']:
            raise ValueError('Decision/model lead or availability mismatch')
        if not np.isfinite(float(row['prediction'])) or float(row['mase_scale']) <= 0:
            raise ValueError('Invalid point or frozen scale')


def first_commit_guard(folder, require_receipt=True):
    folder = Path(folder)
    relative = str((folder/'predictions.csv').relative_to(ROOT))
    commits = subprocess.check_output(['git', 'rev-list', '--reverse', 'HEAD', '--', relative], cwd=ROOT, text=True).splitlines()
    if not commits:
        raise ValueError('Forecast not committed')
    first = commits[0]
    freeze = json.loads((folder/'freeze.json').read_text())
    for name, expected in {**freeze['files'], 'freeze.json': sha(folder/'freeze.json')}.items():
        path = folder/name
        if sha(path) != expected:
            raise ValueError('Frozen local artifact changed:'+name)
        original = subprocess.check_output(['git', 'show', first+':'+str(path.relative_to(ROOT))], cwd=ROOT)
        if hashlib.sha256(original).hexdigest() != expected:
            raise ValueError('Frozen artifact differs from first forecast commit:'+name)
    registration = json.loads((folder/'runtime_registration.json').read_text())
    for name, expected in registration['inputs'].items():
        if sha(ROOT/name) != expected:
            raise ValueError('Issue-time frozen scoring/runtime dependency changed:'+name)
    for name, expected in registration.get('provider_code_files', {}).items():
        if sha(name) != expected:
            raise ValueError('Issue-time installed provider code changed:'+name)
    stamp = subprocess.check_output(['git', 'show', '-s', '--format=%cI', first], cwd=ROOT, text=True).strip()
    committed = aware(datetime.fromisoformat(stamp))
    issued = aware(datetime.fromisoformat(freeze['issued_utc']))
    number = freeze['number']
    issuance_gate(number, issued)
    if not issued <= committed <= planned(number)+timedelta(minutes=59):
        raise ValueError('Commit outside actual issuance/publication contract')
    if require_receipt:
        receipt = json.loads((folder/'public_receipt.json').read_text())
        observed = aware(datetime.fromisoformat(receipt['observed_utc']))
        if receipt['first_forecast_commit'] != first or receipt['predictions_sha256'] != sha(folder/'predictions.csv') or not committed <= observed <= planned(number)+timedelta(minutes=59):
            raise ValueError('Missing/late observed public receipt')
    return first


def score_cases(predictions, actuals, number):
    rows = predictions.to_dict('records')
    case_matrix(rows, number)
    output = []
    for row in rows:
        value = actuals.loc[pd.Timestamp(row['date']), row['state']]
        if not np.isfinite(value) or value <= 0:
            raise ValueError('Missing/nonpositive recorded target: never impute or drop cases')
        result = dict(row, actual=float(value), MAE_GWh=abs(float(value)-row['prediction']))
        result['MASE'] = result['MAE_GWh']/row['mase_scale']
        if row['model'] in ['chronos', 'timesfm']:
            q = np.array([float(row[f'q_{k*100:03d}']) for k in range(1, 10)])
            if not np.isfinite(q).all():
                raise ValueError('Missing native quantiles')
            levels = np.arange(1, 10)/10
            result['scaled_pinball'] = float(np.maximum(levels*(value-q), (levels-1)*(value-q)).mean()/row['mase_scale'])
            lo, median, hi = q[0], q[4], q[8]
            result['native_common_crossing_pairs'] = int((np.diff(q) < 0).sum())
            result['coverage80'] = float(lo <= value <= hi) if lo <= hi else np.nan
            result['scaled_width80'] = float((hi-lo)/row['mase_scale']) if lo <= hi else np.nan
            result['scaled_WIS80_median'] = float((.5*abs(value-median)+.1*(hi-lo+10*max(lo-value, 0)+10*max(value-hi, 0)))/1.5/row['mase_scale']) if lo <= hi else np.nan
        output.append(result)
    return pd.DataFrame(output)


def metrics(cases):
    fields = ['MAE_GWh', 'MASE', 'scaled_pinball', 'coverage80', 'scaled_width80', 'scaled_WIS80_median']
    tables = []
    for scope in ['all', 'outside_named_windows']+FAMILIES:
        if scope == 'all':
            group = cases
        elif scope == 'outside_named_windows':
            group = cases[cases.event_families.fillna('').eq('')]
        else:
            group = cases[cases.event_families.fillna('').map(lambda x: scope in x.split('|'))]
        if group.empty:
            continue
        records = []
        for key, block in group.groupby(['model', 'arm', 'decision_lead']):
            row = dict(zip(['model', 'arm', 'decision_lead'], key), scope=scope, cases=len(block), states=block.state.nunique())
            for field in fields:
                if field in block and block[field].notna().any():
                    # No dropping invalid interval cases from an aggregate.
                    row[field] = float(block.groupby('state')[field].mean().mean()) if block[field].notna().all() else np.nan
            records.append(row)
        tables.append(pd.DataFrame(records))
    return pd.concat(tables, ignore_index=True)
