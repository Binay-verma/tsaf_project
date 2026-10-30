"""Separate stdlib reconstruction of pooled cases, labels, scores and contrasts."""
from collections import defaultdict
import csv
from datetime import date, timedelta
import hashlib
import json
import math
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'results/pooled_festival_v1'
MODELS = {'ridge', 'lightgbm', 'lightgbm_capacity2', 'sarimax', 'chronos', 'timesfm'}
NEW = {'pooled_day1', 'pooled_day5', 'pooled_window1', 'pooled_window5', 'zero1'}
REUSED = {'calendar', 'day5', 'window5'}
PAIRS = {('day5', 'pooled_day5'), ('window5', 'pooled_window5'),
    ('pooled_day5', 'pooled_day1'), ('pooled_window5', 'pooled_window1'),
    ('pooled_day1', 'zero1'), ('pooled_window1', 'zero1'), ('zero1', 'calendar')}


def read(path):
    with path.open(newline='') as stream:
        return list(csv.DictReader(stream))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def case(r):
    return (r['family'], r['state'], int(r['year']), date.fromisoformat(r['origin']),
        date.fromisoformat(r['date']), int(r['horizon']))


def close(a, b):
    assert math.isclose(a, float(b), rel_tol=1e-10, abs_tol=1e-9), (a, b)


def key(r):
    return r['family'], r['model'], r['arm'], r['state'], int(r['year']), int(r['horizon'])


def main():
    protection = json.loads((OUT/'protected_prior_files.json').read_text())
    for name, expected in protection.items():
        assert sha(ROOT/name) == expected, name
    source = read(ROOT/'data/external/latest_state_energy_GWh.csv')
    dc = next(iter(source[0])); labels = {}
    for r in source:
        d = date.fromisoformat(r[dc])
        for state in ['Delhi', 'Karnataka', 'Maharashtra']:
            value = float(r[state]) if r[state] else math.nan
            if math.isfinite(value) and value > 0:
                labels[state, d] = value
    scales = {}
    for state in ['Delhi', 'Karnataka', 'Maharashtra']:
        for year in [2024, 2025]:
            end = date(year-1, 12, 31); start = end-timedelta(days=729)
            diffs = []
            for i in range(7, 730):
                d = start+timedelta(days=i); previous = d-timedelta(days=7)
                if (state, d) in labels and (state, previous) in labels:
                    diffs.append(abs(labels[state, d]-labels[state, previous]))
            scales[state, year] = mean(diffs)
    registration = json.loads((OUT/'registration.json').read_text())
    summaries = {}
    for cohort, parent in [('event', 'festival_features_v1'), ('non_event', 'festival_feature_spillover_v2')]:
        out = OUT/cohort
        p = json.loads((out/'protocol.json').read_text())
        assert sha(out/'protocol.json') == registration['protocols'][cohort]
        assert sha(OUT/'protected_prior_files.json') == p['protection_manifest_sha256']
        for name, expected in p['input_hashes'].items():
            assert sha(ROOT/name) == expected, name
        for name, expected in p['design_hashes'].items():
            assert sha(out/name) == expected, name
        parent_out = ROOT/'results'/parent
        assert sha(parent_out/'primary_cases.csv') == sha(out/'primary_cases.csv')
        assert sha(out/'primary_cases.csv') == sha(out/'window_cases.csv')
        expected = {case(r) for r in read(out/'primary_cases.csv')}
        assert len(expected) == 72
        prior = {(r['model'], r['arm'], case(r)): r for r in read(parent_out/'predictions_primary.csv') if r['arm'] in REUSED}
        new = {}
        for model in MODELS:
            run = json.loads((out/model/'run.json').read_text())
            assert run['protocol_sha256'] == sha(out/'protocol.json')
            assert run['predictions_sha256'] == sha(out/model/'predictions.csv')
            rows = read(out/model/'predictions.csv')
            assert len(rows) == run['rows'] == 360
            for r in rows:
                k = model, r['arm'], case(r)
                assert k not in new and r['model'] == model and r['arm'] in NEW
                new[k] = r
        raw = read(out/'predictions_primary.csv')
        assert len(raw) == 3456
        sets, cells, unique = defaultdict(set), {}, set()
        for r in raw:
            c = case(r); model, arm = r['model'], r['arm']
            unique_key = model, arm, c
            assert unique_key not in unique and c in expected
            unique.add(unique_key); sets[model, arm].add(c)
            assert c[4]-c[3] == timedelta(days=c[-1]-1)
            predicted, actual, scale = map(float, [r['prediction'], r['actual'], r['mase_scale']])
            assert all(math.isfinite(x) for x in [predicted, actual, scale]) and scale > 0
            close(actual, labels[c[1], c[4]]); close(scale, scales[c[1], c[2]])
            original = (prior if arm in REUSED else new)[unique_key]
            for field in ['prediction', 'actual', 'mase_scale']:
                # CSV parse/write may change the final decimal; no forecast is recomputed.
                close(float(original[field]), r[field])
            mae = abs(predicted-actual)
            k = key(r)
            assert k not in cells, 'Anchor cohort has exactly one target per state/year/family/lead'
            cells[k] = (mae, mae/scale)
        assert set(sets) == {(m, a) for m in MODELS for a in NEW | REUSED}
        assert all(v == expected for v in sets.values())
        metrics = read(out/'primary_metrics_state_year.csv')
        assert len(metrics) == len(cells)
        for r in metrics:
            assert int(r['n']) == 1
            mae, mase = cells[key(r)]
            close(mae, r['MAE_GWh']); close(mase, r['MASE'])
        years = defaultdict(list)
        for (family, model, arm, state, year, h), (_, mase) in cells.items():
            years[family, model, arm, year, h].append(mase)
        families, balanced = defaultdict(list), defaultdict(list)
        for (family, model, arm, year, h), values in years.items():
            families[family, model, arm, h].append(mean(values))
        for (family, model, arm, h), values in families.items():
            assert len(values) == 2
            balanced[model, arm, h].append(mean(values))
        for r in read(out/'primary_metrics_festival.csv'):
            close(mean(families[r['family'], r['model'], r['arm'], int(r['horizon'])]), r['MASE'])
        for r in read(out/'primary_metrics_balanced.csv'):
            v = balanced[r['model'], r['arm'], int(r['horizon'])]
            assert len(v) == 5
            close(mean(v), r['MASE'])
        cy = defaultdict(list); pct_year = defaultdict(list)
        seen = set()
        for r in read(out/'contrasts_state_year.csv'):
            arm, reference = r['arm'], r['reference']
            assert (arm, reference) in PAIRS
            k = key(r); baseline = k[0], k[1], reference, k[3], k[4], k[5]
            seen.add((arm, reference, k[0], k[1], k[3], k[4], k[5]))
            mae, mase = cells[k]; bmae, bmase = cells[baseline]
            delta = mase-bmase
            close(delta, r['MASE_change']); close(mae-bmae, r['MAE_change_GWh'])
            pct = 100*(1-mae/bmae) if bmae else None
            if pct is None:
                assert r['percentage_defined'] == 'False' and r['MAE_reduction_pct'] in ['', 'nan', 'NaN']
            else:
                assert r['percentage_defined'] == 'True'
                assert math.isclose(pct, float(r['MAE_reduction_pct']), rel_tol=1e-10, abs_tol=1e-7)
            group = k[0], k[1], arm, reference, k[4], k[5]
            cy[group].append(delta); pct_year[group].append(pct)
        assert len(seen) == 7*6*72
        cf, pf = defaultdict(list), defaultdict(list)
        for (family, model, arm, reference, year, h), values in cy.items():
            cf[family, model, arm, reference, h].append(mean(values))
            vals = pct_year[family, model, arm, reference, year, h]
            pf[family, model, arm, reference, h].append(None if None in vals else mean(vals))
        cb, pb = defaultdict(list), defaultdict(list)
        for k, values in cf.items():
            family, model, arm, reference, h = k
            assert len(values) == 2
            cb[model, arm, reference, h].append(mean(values))
            pb[model, arm, reference, h].append(None if None in pf[k] else mean(pf[k]))
        for r in read(out/'contrasts_balanced.csv'):
            k = r['model'], r['arm'], r['reference'], int(r['horizon'])
            assert len(cb[k]) == 5
            close(mean(cb[k]), r['MASE_change'])
            if None in pb[k]:
                assert r['percentage_defined'] == 'False'
            else:
                assert r['percentage_defined'] == 'True'
                assert math.isclose(mean(pb[k]), float(r['MAE_reduction_pct']), rel_tol=1e-10, abs_tol=1e-7)
        summaries[cohort] = dict(status='pass', rows=len(raw), new_rows=len(new), reused_rows=len(prior),
            cells=len(cells), contrasts=len(seen), identical_cases_per_model_arm=72,
            source_labels_scales_hierarchy_and_paired_changes=True,
            combined_sha256=sha(out/'predictions_primary.csv'))
    result = dict(status='pass', scope='Separate stdlib internal audit; no independent human review or source/overlap certification',
        previous_artifact_hashes_unchanged=len(protection), cohorts=summaries)
    (OUT/'independent_audit.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
