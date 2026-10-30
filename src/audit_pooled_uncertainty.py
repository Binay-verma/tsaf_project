"""Independent stdlib check of native quantile losses/interval arithmetic."""
from collections import defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'results/pooled_festival_v1'
METRICS = ['scaled_mean_pinball', 'coverage80', 'below80', 'above80', 'scaled_width80', 'scaled_interval_score80', 'scaled_WIS80_median']


def read(path):
    with path.open(newline='') as stream:
        return list(csv.DictReader(stream))


def close(a, b):
    if a is None:
        assert b in ['', 'nan', 'NaN']
    else:
        assert math.isclose(a, float(b), rel_tol=1e-10, abs_tol=1e-9), (a, b)


def average(values):
    return None if None in values else mean(values)


def main():
    protocol = json.loads((OUT/'probabilistic_protocol.json').read_text())
    run = json.loads((OUT/'probabilistic_run.json').read_text())
    assert hashlib.sha256((OUT/'probabilistic_protocol.json').read_bytes()).hexdigest() == run['protocol_sha256']
    assert hashlib.sha256((ROOT/'src/score_pooled_uncertainty.py').read_bytes()).hexdigest() == protocol['scoring_source_sha256']
    summaries = {}
    for cohort in ['event', 'non_event']:
        out = OUT/cohort
        combined = read(out/'predictions_primary.csv')
        source = {(r['family'], r['model'], r['arm'], r['state'], int(r['year']), int(r['horizon'])): r
            for r in combined if r['model'] in ['chronos', 'timesfm']}
        rows = read(out/'native_uncertainty_cases.csv')
        assert len(rows) == len(source) == 1152
        cells = {}; invalid_groups = set()
        for r in rows:
            k = r['family'], r['model'], r['arm'], r['state'], int(r['year']), int(r['horizon'])
            assert k not in cells
            original = source[k]
            y, scale = float(original['actual']), float(original['mase_scale'])
            q = [float(original[f'q_{i*100:03d}']) for i in range(1, 10)]
            assert all(math.isfinite(x) for x in q)
            losses = []
            for i, value in enumerate(q, 1):
                tau = i/10; error = y-value
                losses.append(tau*error if error >= 0 else (tau-1)*error)
                close(value, r[f'q_{i*100:03d}'])
            lower, median, upper = q[0], q[4], q[8]
            bad = lower > upper
            assert r['invalid80'] == str(bad)
            assert int(r['common_adjacent_crossings']) == sum(a > b for a, b in zip(q, q[1:]))
            interval = upper-lower
            if y < lower:
                interval += (2/.2)*(lower-y)
            if y > upper:
                interval += (2/.2)*(y-upper)
            values = dict(scaled_mean_pinball=mean(losses)/scale,
                coverage80=None if bad else float(lower <= y <= upper),
                below80=None if bad else float(y < lower), above80=None if bad else float(y > upper),
                scaled_width80=None if bad else (upper-lower)/scale,
                scaled_interval_score80=None if bad else interval/scale,
                scaled_WIS80_median=None if bad else (.5*abs(y-median)+.1*interval)/(1.5*scale))
            if bad:
                invalid_groups.add((k[1], k[2], k[-1]))
            close(None if bad else upper-lower, r['width80_GWh'])
            for metric in METRICS:
                close(values[metric], r[metric])
            cells[k] = values
        years = defaultdict(lambda: defaultdict(list))
        for (family, model, arm, state, year, h), values in cells.items():
            for metric, value in values.items():
                years[family, model, arm, year, h][metric].append(value)
        families = defaultdict(lambda: defaultdict(list))
        for (family, model, arm, year, h), values in years.items():
            for metric, numbers in values.items():
                families[family, model, arm, h][metric].append(average(numbers))
        balanced = defaultdict(lambda: defaultdict(list))
        for (family, model, arm, h), values in families.items():
            for metric, numbers in values.items():
                value = average(numbers)
                if (model, arm, h) in invalid_groups and metric != 'scaled_mean_pinball':
                    value = None
                balanced[model, arm, h][metric].append(value)
        for r in read(out/'native_uncertainty_balanced.csv'):
            k = r['model'], r['arm'], int(r['horizon'])
            for metric, numbers in balanced[k].items():
                assert len(numbers) == 5
                close(average(numbers), r[metric])
        summaries[cohort] = dict(cases=len(cells), invalid_endpoint_groups=len(invalid_groups),
            complete_native_quantiles=True, all_case_arithmetic_and_macro_weights_checked=True)
    result = dict(status='pass', scope='Separate internal stdlib arithmetic/aggregation audit, not proof of calibration or human review', cohorts=summaries)
    (OUT/'probabilistic_audit.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
