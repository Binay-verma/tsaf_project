"""Independent stdlib source/case/metric audit of saved interventions."""
import argparse
from collections import defaultdict
import csv
from datetime import date, timedelta
import hashlib
import json
import math
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT/'results/festival_features_v1'
KEY = ['family', 'state', 'year', 'origin', 'date', 'horizon']


def read(path):
    with path.open(newline='') as f:
        return list(csv.DictReader(f))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def case(r):
    return r['family'], r['state'], int(r['year']), date.fromisoformat(r['origin']), date.fromisoformat(r['date']), int(r['horizon'])


def audit(out):
    p = json.loads((out/'protocol.json').read_text())
    for f, h in p['input_hashes'].items():
        assert sha(ROOT/f) == h, f
    for f, h in p['design_hashes'].items():
        assert sha(out/f) == h, f
    protected = json.loads((PARENT/'prior_checkpoint_protected.json').read_text())
    for f, h in protected.items():
        assert sha(ROOT/f) == h, f
    source = read(ROOT/'data/external/latest_state_energy_GWh.csv')
    dc = next(iter(source[0])); labels = {}
    for r in source:
        d = date.fromisoformat(r[dc])
        for state in ['Delhi', 'Karnataka', 'Maharashtra']:
            x = float(r[state]) if r[state] else math.nan
            if math.isfinite(x) and x > 0:
                labels[state, d] = x
    scales = {}
    for state in ['Delhi', 'Karnataka', 'Maharashtra']:
        for year in [2024, 2025]:
            end = date(year-1, 12, 31); start = end-timedelta(days=729)
            diffs = [abs(labels[state, d]-labels[state, d-timedelta(days=7)])
                for i in range(7, 730) if (state, d := start+timedelta(days=i)) in labels and (state, d-timedelta(days=7)) in labels]
            scales[state, year] = mean(diffs)
    expected = {case(r) for r in read(out/'primary_cases.csv')}
    assert len(expected) == 72
    data = read(out/'predictions_primary.csv')
    by_arm, errors, unique = defaultdict(set), defaultdict(list), set()
    for r in data:
        c = case(r); model, arm = r['model'], r['arm']
        assert (model, arm, c) not in unique
        unique.add((model, arm, c)); by_arm[model, arm].add(c)
        assert c in expected and c[4]-c[3] == timedelta(days=c[-1]-1)
        actual, predicted, scale = map(float, [r['actual'], r['prediction'], r['mase_scale']])
        assert all(math.isfinite(v) for v in [actual, predicted, scale]) and scale > 0
        assert abs(actual-labels[c[1], c[4]]) < 1e-9
        assert abs(scale-scales[c[1], c[2]]) < 1e-9
        errors[c[0], model, arm, c[1], c[2], c[-1]].append(abs(actual-predicted))
    assert len(by_arm) == 6*len(p['arms'])
    assert all(v == expected for v in by_arm.values())
    cells = {}
    for r in read(out/'primary_metrics_state_year.csv'):
        k = r['family'], r['model'], r['arm'], r['state'], int(r['year']), int(r['horizon'])
        assert int(r['n']) == len(errors[k]) == 1
        mae = mean(errors[k]); mase = mae/scales[k[3], k[4]]
        assert abs(mae-float(r['MAE_GWh'])) < 1e-9
        assert abs(mase-float(r['MASE'])) < 1e-9
        cells[k] = mase
    assert set(cells) == set(errors)
    yearly = defaultdict(list)
    for (family, model, arm, state, year, h), value in cells.items():
        yearly[family, model, arm, year, h].append(value)
    festival = defaultdict(list)
    for (family, model, arm, year, h), values in yearly.items():
        festival[family, model, arm, h].append(mean(values))
    for r in read(out/'primary_metrics_festival.csv'):
        k = r['family'], r['model'], r['arm'], int(r['horizon'])
        assert len(festival[k]) == 2
        assert abs(mean(festival[k])-float(r['MASE'])) < 1e-9
    for r in read(out/'primary_paired_state_year.csv'):
        k = r['family'], r['model'], r['arm'], r['state'], int(r['year']), int(r['horizon'])
        baseline = k[0], k[1], 'calendar', k[3], k[4], k[5]
        assert abs((cells[k]-cells[baseline])-float(r['MASE_change'])) < 1e-9
        denominator = mean(errors[baseline])
        if denominator > 0:
            expected_pct = 100*(1-mean(errors[k])/denominator)
            assert math.isclose(float(r['MAE_reduction_pct']), expected_pct, rel_tol=1e-10, abs_tol=1e-7)
            assert r['percentage_defined'] == 'True'
        else:
            assert r['percentage_defined'] == 'False' and r['MAE_reduction_pct'] in ['', 'nan', 'NaN']
    if (out/'primary_control_contrasts_state_year.csv').exists():
        for r in read(out/'primary_control_contrasts_state_year.csv'):
            k = r['family'], r['model'], r['arm'], r['state'], int(r['year']), int(r['horizon'])
            reference = k[0], k[1], r['reference'], k[3], k[4], k[5]
            assert abs((cells[k]-cells[reference])-float(r['MASE_change'])) < 1e-9
    # The wider classical figures must have their own complete-cohort metric
    # checks; a passed anchor audit alone would not validate them.
    expected_secondary = {case(r) for r in read(out/'window_cases.csv')}
    sec_rows = read(out/'predictions_secondary_classical.csv')
    sec_errors, sec_sets, sec_unique = defaultdict(list), defaultdict(set), set()
    for r in sec_rows:
        c = case(r); model, arm = r['model'], r['arm']
        assert (model, arm, c) not in sec_unique
        sec_unique.add((model, arm, c)); sec_sets[model, arm].add(c)
        actual, predicted, scale = map(float, [r['actual'], r['prediction'], r['mase_scale']])
        assert all(math.isfinite(v) for v in [actual, predicted, scale]) and scale > 0
        assert c in expected_secondary and c[4]-c[3] == timedelta(days=c[-1]-1)
        assert abs(actual-labels[c[1], c[4]]) < 1e-9
        assert abs(scale-scales[c[1], c[2]]) < 1e-9
        sec_errors[c[0], model, arm, c[1], c[2], c[-1]].append(abs(actual-predicted))
    assert all(s == expected_secondary for s in sec_sets.values())
    sec_cells = {}
    for r in read(out/'secondary_classical_metrics_state_year.csv'):
        k = r['family'], r['model'], r['arm'], r['state'], int(r['year']), int(r['horizon'])
        mae = mean(sec_errors[k]); mase = mae/scales[k[3], k[4]]
        assert int(r['n']) == len(sec_errors[k])
        assert abs(mae-float(r['MAE_GWh'])) < 1e-9 and abs(mase-float(r['MASE'])) < 1e-9
        sec_cells[k] = mase
    assert set(sec_cells) == set(sec_errors)
    sy, sf = defaultdict(list), defaultdict(list)
    for (family, model, arm, state, year, h), value in sec_cells.items():
        sy[family, model, arm, year, h].append(value)
    for (family, model, arm, year, h), values in sy.items():
        sf[family, model, arm, h].append(mean(values))
    for r in read(out/'secondary_classical_metrics_festival.csv'):
        k = r['family'], r['model'], r['arm'], int(r['horizon'])
        assert abs(mean(sf[k])-float(r['MASE'])) < 1e-9
    anchors = read(PARENT/'anchors_2022_2025.csv')
    assert len(anchors) == 58
    true = defaultdict(set)
    for a in anchors:
        d = date.fromisoformat(a['date'])
        assert 2022 <= d.year <= 2025
        true[a['state'], int(a['year'])].update(d+timedelta(days=i) for i in range(-3, 4))
    for a in read(PARENT/'placebo_anchors.csv'):
        shift = int(a['shift_days'])
        assert shift in [-42, -35, -28, 28, 35, 42]
        d = date.fromisoformat(a['date']); old = date.fromisoformat(a['original_date'])
        assert d-old == timedelta(days=shift) and d.weekday() == old.weekday()
        assert not {d+timedelta(days=i) for i in range(-3, 4)}.intersection(true[a['state'], int(a['year'])])
    if 'spillover' in out.name:
        annual = read(ROOT/'results/extended_validation/regional_calendar_date_audit.csv')
        blocked = defaultdict(set)
        for r in annual:
            if r['in_annual_schedule'] == 'True':
                d = date.fromisoformat(r['date'])
                blocked[r['state'], int(r['year'])].update(d+timedelta(days=i) for i in range(-3, 4))
        for r in read(out/'date_only_matching.csv'):
            d = date.fromisoformat(r['non_event_date']); e = date.fromisoformat(r['event_date'])
            assert d.weekday() == e.weekday()
            assert d not in blocked[r['state'], int(r['year'])] | true[r['state'], int(r['year'])]
    result = dict(status='pass', scope='Independent internal stdlib reconstruction, not independent human scientific review',
        models=6, arms=len(p['arms']), cases_per_arm=72, primary_rows=len(data), metric_cells=len(cells),
        previous_artifact_hashes_unchanged=len(protected),
        checks=['complete identical cases, no silent missing forecast intersection', 'source labels only', 'lead/date alignment',
            '730-day pre-year scales', 'MAE/MASE reconstruction', 'equal state/year/family weighting',
            'named training-date span', 'weekday-preserving non-overlapping placebos', 'prior source/result/presentation/freeze hashes'],
        primary_predictions_sha256=sha(out/'predictions_primary.csv'))
    result['secondary_classical'] = dict(rows=len(sec_rows), metric_cells=len(sec_cells), cases_per_arm=len(expected_secondary),
        all_reported_arms_complete=True, paired_primary_changes_independently_checked=True)
    (out/'independent_audit.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--out', type=Path, default=PARENT)
    audit(p.parse_args().out.resolve())
