"""Independent stdlib checks of multi-festival persisted labels/cases/metrics.

Does not import experiment feature, fitting or scoring helpers. This is an
internal software audit, not independent human scientific review.
"""
import argparse
import csv
from collections import defaultdict
from datetime import date, timedelta
import hashlib
import json
import math
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'results/multifestival_cached_v1'


def read(path):
    with path.open(newline='') as f:
        return list(csv.DictReader(f))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(out):
    protocol = json.loads((BASE/'protocol.json').read_text())
    for p, h in protocol['input_hashes'].items():
        assert sha(ROOT/p) == h, p
    for p, h in protocol['design_hashes'].items():
        assert sha(BASE/p) == h, p
    source = read(ROOT/'data/external/latest_state_energy_GWh.csv')
    datecol = next(iter(source[0]))
    labels = {}
    for r in source:
        d = date.fromisoformat(r[datecol])
        for state in ['Delhi', 'Karnataka', 'Maharashtra']:
            v = float(r[state]) if r[state] else math.nan
            if math.isfinite(v) and v > 0:
                labels[state, d] = v
    scales = {}
    for state in ['Delhi', 'Karnataka', 'Maharashtra']:
        for year in [2024, 2025]:
            end = date(year-1, 12, 31)
            start = end-timedelta(days=729)
            diffs = [abs(labels[state, d]-labels[state, d-timedelta(days=7)])
                for i in range(7, 730) if (state, d := start+timedelta(days=i)) in labels and
                (state, d-timedelta(days=7)) in labels]
            scales[state, year] = mean(diffs)
    anchors = defaultdict(set)
    for r in read(BASE/'anchors.csv'):
        anchor = date.fromisoformat(r['date'])
        anchors[r['family'], r['state'], int(r['year'])].update(anchor+timedelta(days=i) for i in range(-3, 4))
    expected = {(family, state, year, target-timedelta(days=h-1), target, h)
        for (family, state, year), targets in anchors.items() for target in targets for h in [1, 7, 14]}
    case = lambda r: (r['family'], r['state'], int(r['year']), date.fromisoformat(r['origin']), date.fromisoformat(r['date']), int(r['horizon']))
    assert {case(r) for r in read(BASE/'expected_cases.csv')} == expected
    eligible = {k for k in expected if (k[1], k[4]) in labels}
    assert {case(r) for r in read(BASE/'excluded_labels.csv')} == expected-eligible
    rows = read(out/'predictions.csv')
    unique, byconfig, errors = set(), defaultdict(set), defaultdict(list)
    for r in rows:
        c = case(r)
        config = r['configuration']
        assert (config, c) not in unique, (config, c)
        unique.add((config, c))
        byconfig[config].add(c)
        assert c in eligible
        assert c[4]-c[3] == timedelta(days=c[-1]-1)
        actual, predicted, scale = map(float, [r['actual'], r['prediction'], r['mase_scale']])
        assert all(math.isfinite(x) for x in [actual, predicted, scale]) and scale > 0
        assert abs(actual-labels[c[1], c[4]]) < 1e-9
        assert abs(scale-scales[c[1], c[2]]) < 1e-9
        errors[c[0], config, c[1], c[2], c[-1]].append(abs(actual-predicted))
    assert all(s == eligible for s in byconfig.values())
    cells = {}
    for r in read(out/'metrics_state_year.csv'):
        k = r['family'], r['configuration'], r['state'], int(r['year']), int(r['horizon'])
        assert len(errors[k]) == int(r['n'])
        mae = mean(errors[k])
        assert abs(mae-float(r['MAE_GWh'])) < 1e-9
        mase = mae/scales[k[2], k[3]]
        assert abs(mase-float(r['MASE'])) < 1e-9
        cells[k] = mase
    assert set(cells) == set(errors)
    states = defaultdict(list)
    for (family, config, state, year, horizon), value in cells.items():
        states[family, config, year, horizon].append(value)
    years = defaultdict(list)
    for (family, config, year, horizon), values in states.items():
        years[family, config, horizon].append(mean(values))
    for r in read(out/'metrics_festival.csv'):
        k = r['family'], r['configuration'], int(r['horizon'])
        assert abs(mean(years[k])-float(r['MASE'])) < 1e-9
        assert len(years[k]) == int(r['years']) == 2
    # Preserve all files that existed before this extension, including the
    # original frozen future forecasts. Documentation may be updated afterwards.
    old = json.loads((ROOT/'GITHUB_CHECKSUMS_20261030.json').read_text())
    protected = {p: h for p, h in old['files'].items() if p.startswith(('data/', 'results/extended_validation/', 'results/prospective_20261030_v1/'))}
    for p, h in protected.items():
        assert sha(ROOT/p) == h, p
    result = dict(status='pass', audit='Internal independent stdlib reconstruction; not external human review',
        configurations=len(byconfig), expected_memberships=len(expected), scored_memberships_per_configuration=len(eligible),
        rows=len(rows), state_year_metric_cells=len(cells), protected_files_unchanged=len(protected),
        checks=['anchor-to-window reconstruction', 'same complete cases for every configuration',
            'recorded source labels only', 'origin+h-1 target alignment', 'independent730-day pre-year scales',
            'MAE/MASE reconstruction', 'equal-state/equal-year aggregation', 'original/frozen artifact hashes'],
        hashes={p: sha(out/p) for p in ['predictions.csv', 'metrics_state_year.csv', 'metrics_festival.csv']})
    (out/'independent_audit.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, default=BASE)
    audit(parser.parse_args().out.resolve())
