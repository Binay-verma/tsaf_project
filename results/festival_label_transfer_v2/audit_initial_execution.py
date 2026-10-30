"""Separate saved-output audit; imports no experiment or model helpers."""
from collections import defaultdict
from datetime import date, timedelta
import hashlib
import json
import math
from pathlib import Path
from statistics import mean
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'results/festival_label_transfer_v2'
FAMILIES = ['Holi', 'Dussehra', 'Ganesh_Chaturthi', 'Ugadi_Gudi_Padwa', 'Diwali']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def close(a, b):
    assert math.isclose(float(a), float(b), rel_tol=1e-10, abs_tol=1e-9), (a, b)


def main():
    p = json.loads((OUT/'protocol.json').read_text())
    for f, h in p['input_hashes'].items():
        assert sha(ROOT/f) == h, f
    assert sha(OUT/'matching_preflight.json') == p['matching_preflight_sha256']
    assert sha(OUT/'cases.csv') == p['cases_sha256']
    protection = json.loads((ROOT/'results/pooled_festival_v1/protected_prior_files.json').read_text())
    for f, h in protection.items():
        assert sha(ROOT/f) == h, f
    data = pd.read_csv(ROOT/'data/external/latest_state_energy_GWh.csv', index_col=0, parse_dates=True).asfreq('D')
    ledger = pd.read_csv(ROOT/'results/festival_features_v1/anchors_2022_2025.csv', parse_dates=['date'])
    annual = pd.read_csv(ROOT/'results/extended_validation/regional_calendar_date_audit.csv', parse_dates=['date'])
    cases = pd.read_csv(OUT/'cases.csv')
    casekey = ['cohort', 'family', 'state', 'year', 'origin', 'date', 'horizon']
    expected = set(map(tuple, cases[casekey].to_numpy()))
    assert len(expected) == 144
    preflight = {(r['state'], r['year'], r['horizon'], r['family'], r['refit']): r for r in json.loads((OUT/'matching_preflight.json').read_text())}
    assert len(preflight) == 141
    summaries, shifts = {}, []
    for worker in p['workers']:
        out = OUT/worker
        run = json.loads((out/'run.json').read_text())
        assert run['protocol_sha256'] == sha(OUT/'protocol.json')
        assert run['predictions_sha256'] == sha(out/'predictions.csv')
        fits = json.loads((out/'fit_log.json').read_text())
        assert len(fits) == run['fits'] == 141*9
        groups = defaultdict(list)
        for r in fits:
            state, h = r['state'], int(r['horizon'])
            refit = pd.Timestamp(r['refit']); cutoff = refit-pd.Timedelta(days=1)
            dates = pd.date_range(cutoff-pd.Timedelta(days=729)+pd.Timedelta(days=h-1), cutoff)
            labels = data[state].reindex(dates)
            dates = dates[labels.notna() & labels.gt(0)]
            assert len(dates) == r['candidate_training_n'] == r['training_n']
            assert dates.min() >= pd.Timestamp('2022-01-01') and dates.max() < refit
            assert pd.Timestamp(r['training_target_max']) <= cutoff
            rows = cases[cases.state.eq(state) & cases.year.eq(r['year']) & cases.horizon.eq(h) & cases.family.eq(r['family'])]
            origins = pd.to_datetime(rows.origin)
            rows = rows[origins.dt.to_period('M').eq(refit.to_period('M'))]
            assert len(rows) and pd.to_datetime(rows.origin).min() >= refit
            family_anchors = ledger[ledger.state.eq(state) & ledger.family.eq(r['family'])].date
            own_window = {d for a in family_anchors for d in pd.date_range(a-pd.Timedelta(days=3), a+pd.Timedelta(days=3))}
            excluded = sorted(set(dates) & own_window)
            prohibited_anchors = list(annual[annual.state.eq(state) & annual.in_annual_schedule].date)+list(ledger[ledger.state.eq(state)].date)
            blocked = {d for a in prohibited_anchors for d in pd.date_range(a-pd.Timedelta(days=3), a+pd.Timedelta(days=3))}
            chosen, pairs = set(), []
            for target in excluded:
                candidates = [target+pd.Timedelta(days=shift) for shift in p['matching_shifts_days']]
                eligible = [d for d in candidates if d in set(dates) and d.year == target.year and d not in blocked and d not in chosen]
                assert eligible
                control = eligible[0]; chosen.add(control)
                pairs.append(dict(family_label_date=str(target.date()), matched_control_date=str(control.date()), shift_days=int((control-target).days)))
            ident = state, r['year'], h, r['family'], r['refit']
            assert pairs == preflight[ident]['matches']
            expected_drop = set(excluded) if r['policy'] == 'exclude_family' else chosen if r['policy'] == 'exclude_control' else set()
            assert set(pd.to_datetime(r['dropped_label_dates'])) == expected_drop
            retained = dates[~dates.isin(expected_drop)]
            assert len(retained) == r['retained_training_n'] >= 365
            assert len(expected_drop) == r['dropped_n']
            encoded = '|'.join(str(d.date()) for d in retained).encode()
            assert hashlib.sha256(encoded).hexdigest() == r['fitting_label_dates_sha256']
            yy = data[state].reindex(retained).to_numpy()
            assert hashlib.sha256(yy.tobytes()).hexdigest() == r['fitting_y_sha256']
            assert str(retained.min().date()) == r['retained_label_min'] and str(retained.max().date()) == r['retained_label_max']
            if worker == 'ridge_fixed10':
                assert r['parameters'] == {'alpha': 10.}
            else:
                assert r['parameters'] == {**p['tree_parameters'], 'min_child_samples': p['leaf_minimum'][worker]}
            assert r['feature_count'] == (40 if r['feature'] == 'calendar' else 45)
            if r['feature'] == 'calendar':
                support = []
            elif r['feature'] == 'pooled_day5':
                support = [int(retained.isin(ledger[ledger.state.eq(state)].date).sum())]+[0]*4
            else:
                support = [int(retained.isin(ledger[ledger.state.eq(state) & ledger.family.eq(f)].date).sum()) for f in FAMILIES]
            assert support == r['nonzero_added_features']
            if r['feature'] == 'typed_day5' and r['policy'] == 'exclude_family':
                assert support[FAMILIES.index(r['family'])] == 0
            groups[ident].append(r)
        for ident, logs in groups.items():
            assert {(r['feature'], r['policy']) for r in logs} == {(f, q) for f in p['feature_arms'] for q in p['row_policies']}
            for policy in p['row_policies']:
                assert len({r['fitting_y_sha256'] for r in logs if r['policy'] == policy}) == 1
            held = [r['retained_training_n'] for r in logs if r['policy'] == 'exclude_family']
            ctrl = [r['retained_training_n'] for r in logs if r['policy'] == 'exclude_control']
            assert held == ctrl
        for ident, r in preflight.items():
            if worker == p['workers'][0]:
                shifts.extend({**dict(state=ident[0], year=ident[1], horizon=ident[2], family=ident[3], refit=ident[4]), **pair} for pair in r['matches'])
        summaries[worker] = dict(fits=len(fits), same_count_controls=True, date_only_matches=True,
            fixed_parameters=True, label_bytes_and_dates_reconstructed=True, zero_own_family_typed_support=True,
            exposure_limit='Earlier family responses remain in causal target-history features; not wholly unseen-event exposure')
    d = pd.read_csv(OUT/'predictions.csv')
    assert len(d) == 3888 and not d.duplicated(['model', 'arm']+casekey).any()
    for _, group in d.groupby(['model', 'arm']):
        assert set(map(tuple, group[casekey].to_numpy())) == expected
    scales = {}
    for state in ['Delhi', 'Karnataka', 'Maharashtra']:
        for year in [2024, 2025]:
            end = pd.Timestamp(f'{year-1}-12-31'); tr = data[state].loc[end-pd.Timedelta(days=729):end]
            # Independent explicit pairs rather than importing the scale helper.
            x = tr.to_numpy()
            diffs = [abs(x[i]-x[i-7]) for i in range(7, len(x)) if np.isfinite(x[i]) and np.isfinite(x[i-7])]
            scales[state, year] = mean(diffs)
    cells = {}
    for r in d.itertuples(index=False):
        target, origin = pd.Timestamp(r.date), pd.Timestamp(r.origin)
        assert (target-origin).days == r.horizon-1
        close(r.actual, data.loc[target, r.state]); close(r.mase_scale, scales[r.state, r.year])
        k = r.cohort, r.family, r.model, r.arm, r.state, r.year, r.horizon
        cells[k] = (abs(r.actual-r.prediction), abs(r.actual-r.prediction)/r.mase_scale)
    table = pd.read_csv(OUT/'metrics_state_year.csv')
    assert len(table) == len(cells)
    for r in table.itertuples(index=False):
        k = r.cohort, r.family, r.model, r.arm, r.state, r.year, r.horizon
        assert r.n == 1; close(cells[k][0], r.MAE_GWh); close(cells[k][1], r.MASE)
    years, families, balanced = defaultdict(list), defaultdict(list), defaultdict(list)
    for (cohort, family, model, arm, state, year, h), (_, mase) in cells.items():
        years[cohort, family, model, arm, year, h].append(mase)
    for (cohort, family, model, arm, year, h), values in years.items():
        families[cohort, family, model, arm, h].append(mean(values))
    for (cohort, family, model, arm, h), values in families.items():
        assert len(values) == 2
        balanced[cohort, model, arm, h].append(mean(values))
    for r in pd.read_csv(OUT/'metrics_balanced.csv').itertuples(index=False):
        values = balanced[r.cohort, r.model, r.arm, r.horizon]
        assert len(values) == 5; close(mean(values), r.MASE)
    for r in pd.read_csv(OUT/'contrasts_state_year.csv').itertuples(index=False):
        k = r.cohort, r.family, r.model, r.arm, r.state, r.year, r.horizon
        reference = r.cohort, r.family, r.model, r.reference, r.state, r.year, r.horizon
        close(cells[k][0]-cells[reference][0], r.MAE_change_GWh)
        close(cells[k][1]-cells[reference][1], r.MASE_change)
    for r in pd.read_csv(OUT/'contrasts_balanced.csv').itertuples(index=False):
        close(mean(balanced[r.cohort, r.model, r.arm, r.horizon])-mean(balanced[r.cohort, r.model, r.reference, r.horizon]), r.MASE_change)
    pd.DataFrame(shifts).to_csv(OUT/'control_shift_inventory.csv', index=False)
    result = dict(status='pass', scope='Separate internal date/NumPy/log/metric reconstruction; not human review or historical exposure clearance',
        rows=len(d), workers=summaries, protected_prior_files_unchanged=len(protection),
        matching_blocks=len(preflight), maximum_control_shift_days=max(abs(r['shift_days']) for r in shifts),
        matching_distance_counts=pd.Series([abs(r['shift_days']) for r in shifts]).value_counts().sort_index().to_dict(),
        predictions_sha256=sha(OUT/'predictions.csv'))
    (OUT/'independent_audit.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
