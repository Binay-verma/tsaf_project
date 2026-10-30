"""Calendar-feasible version after retained v1 exact-match failure."""
import argparse
import json
import pandas as pd
import numpy as np
import festival_label_transfer as engine
from festival_feature_design import ROOT, sha, dump
from forecasting import load_data
from robust_baselines import design_frame

OUT = ROOT/'results/festival_label_transfer_v2'
SHIFTS = [sign*days for days in range(28, 85, 7) for sign in [1, -1]]


def removed_dates(train_dates, family_dates, prohibited):
    available = set(pd.DatetimeIndex(train_dates))
    held = sorted(available.intersection({d for a in family_dates for d in pd.date_range(a-pd.Timedelta(days=3), a+pd.Timedelta(days=3))}))
    controls, pairs = set(), []
    for target in held:
        eligible = [target+pd.Timedelta(days=k) for k in SHIFTS]
        eligible = [d for d in eligible if d in available and d.year == target.year and d not in prohibited and d not in controls]
        if not eligible:
            raise ValueError('No exact same-weekday control within28–84days for '+str(target.date()))
        selected = eligible[0]; controls.add(selected)
        pairs.append(dict(family_label_date=str(target.date()), matched_control_date=str(selected.date()), shift_days=int((selected-target).days)))
    assert len(held) == len(controls) and not set(held).intersection(controls)
    return set(held), controls, pairs


def preflight():
    data = load_data('latest')
    cases = pd.read_csv(ROOT/'results/festival_label_transfer_v1/cases.csv', parse_dates=['date', 'origin'])
    ledger = pd.read_csv(ROOT/'results/festival_features_v1/anchors_2022_2025.csv', parse_dates=['date'])
    annual = pd.read_csv(ROOT/'results/extended_validation/regional_calendar_date_audit.csv', parse_dates=['date'])
    rows = []
    for (state, year, h), group in cases.groupby(['state', 'year', 'horizon']):
        base, _ = design_frame(data[state], state, int(h), 'rich_calendar')
        anchors = list(annual[annual.state.eq(state) & annual.in_annual_schedule].date)+list(ledger[ledger.state.eq(state)].date)
        blocked = {d for a in anchors for d in pd.date_range(a-pd.Timedelta(days=3), a+pd.Timedelta(days=3))}
        for (family, month), segment in group.groupby(['family', group.origin.dt.to_period('M')]):
            cutoff = month.start_time-pd.Timedelta(days=1)
            origins = pd.date_range(cutoff-pd.Timedelta(days=729), cutoff-pd.Timedelta(days=int(h)-1))
            dates = origins+pd.Timedelta(days=int(h)-1)
            valid = np.isfinite(base.reindex(origins).to_numpy()).all(axis=1) & data[state].reindex(dates).notna().to_numpy()
            held, controls, matches = removed_dates(dates[valid], ledger[ledger.state.eq(state) & ledger.family.eq(family)].date, blocked)
            assert held and len(held) == len(controls)
            rows.append(dict(state=state, year=int(year), horizon=int(h), family=family, refit=str(month.start_time.date()),
                excluded_rows=len(held), control_rows=len(controls), matches=matches))
    return rows


def prepare():
    if OUT.exists():
        raise FileExistsError('Preserve v2 design/results')
    # This must finish before any v2 protocol or model output is created.
    matches = preflight()
    engine.OUT = OUT
    engine.prepare()
    dump(OUT/'matching_preflight.json', matches)
    p = json.loads((OUT/'protocol.json').read_text())
    p.update(version_note='v1Ridge aborted on2022-08-28because no eligible control exists at28/35/42days. Original partial fits/checkpoint/failure retained, no errors inspected to select this revision. v2extends fixed shifts to28–84days and checks EVERYtraining block before protocol freeze/model execution.',
        control='For each excluded recorded label in chronological order, choose first eligible same-weekday/same-year candidate at+28,-28,+35,-35,...,+84,-84days. Must be in the same candidate training block, distinct, outside+/-3days of every annual/registered holiday. Exact row-count match; stop on infeasibility. Only dates/label availability used; longer shifts weaken seasonal matching and are fully inventoried.',
        matching_shifts_days=SHIFTS, matching_preflight_sha256=sha(OUT/'matching_preflight.json'),
        execution_overrides='Wrapper sets engine.OUT to version2 and engine.removed_dates to its fixed28–84day matcher; original training/model engine unchanged. No version1 results overwritten.')
    for f in ['src/festival_label_transfer_v2.py', 'src/test_festival_label_transfer_v2.py',
        'results/festival_label_transfer_v1/protocol.json', 'results/festival_label_transfer_v1/ridge_fixed10/failure.txt']:
        p['input_hashes'][f] = sha(ROOT/f)
    dump(OUT/'protocol.json', p)
    print('V2 all', len(matches), 'training blocks have exact matching before model execution')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('action', choices=['prepare']+engine.WORKERS)
    args = parser.parse_args()
    if args.action == 'prepare':
        prepare()
    else:
        engine.OUT = OUT; engine.removed_dates = removed_dates
        engine.run(args.action)
