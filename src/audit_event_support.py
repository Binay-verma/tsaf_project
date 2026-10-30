"""Independent scalar reconstruction of every support/proxy/paired association."""
import argparse
from collections import defaultdict, deque
import csv
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'results/event_support_v1'
FAMILIES = ['Holi', 'Dussehra', 'Ganesh_Chaturthi', 'Ugadi_Gudi_Padwa', 'Diwali']
KEY = ['family', 'state', 'year', 'origin', 'date', 'horizon']
METRICS = ['own_support_days', 'own_support_ratio', 'own_prior_year_support_days',
           'heterogeneity_scaled', 'target_flag_active', 'future_own_support_days']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    with Path(path).open(newline='') as stream:
        return list(csv.DictReader(stream))


def close(a, b):
    if b == '' or (isinstance(b, float) and math.isnan(b)):
        assert math.isnan(a), (a, b)
    else:
        assert math.isclose(a, float(b), abs_tol=1e-9, rel_tol=1e-9), (a, b)


def case(row):
    return tuple(row[key] for key in KEY)


def correlation(x, y):
    if len(x) < 3 or len(set(x)) < 2 or len(set(y)) < 2:
        return math.nan
    mx, my = mean(x), mean(y)
    return sum((a-mx)*(b-my) for a, b in zip(x, y))/math.sqrt(
        sum((a-mx)**2 for a in x)*sum((b-my)**2 for b in y))


def ranks(values):
    groups = defaultdict(list)
    for rank, value in enumerate(sorted(values), start=1):
        groups[value].append(rank)
    return [mean(groups[value]) for value in values]


def main(part):
    protocol = json.loads((OUT/'protocol.json').read_text())
    for name, expected in protocol['source_hashes'].items():
        assert sha(ROOT/name) == expected, name
    destination = OUT/('moderator_audit.json' if part == 'moderators' else 'independent_audit.json')
    if destination.exists():
        raise FileExistsError('Preserve prior moderator/association audit')
    build = json.loads((OUT/'moderator_build.json').read_text())
    assert sha(OUT/'moderators.csv') == build['moderators_sha256']
    assert sha(OUT/'protocol.json') == build['protocol_sha256']
    with (ROOT/'data/external/latest_state_energy_GWh.csv').open(newline='') as stream:
        reader = csv.DictReader(stream)
        date_column = reader.fieldnames[0]
        source = {date.fromisoformat(row[date_column]): {state: float(row[state]) if row[state] else math.nan
                  for state in ['Delhi', 'Karnataka', 'Maharashtra']} for row in reader}
    ledger = read(ROOT/'results/calendar_semantics_v2/anchors_2022_2025.csv')
    active = {}
    for state in ['Delhi', 'Karnataka', 'Maharashtra']:
        for representation in ['day', 'window']:
            for family in FAMILIES:
                roots = [date.fromisoformat(row['date']) for row in ledger if row['state'] == state and row['family'] == family]
                active[state, representation, family] = {day+timedelta(days=offset) for day in roots
                    for offset in ([0] if representation == 'day' else range(-3, 4))}
    cases = read(ROOT/'results/calendar_recenter_v1/event_cases_recentered.csv')
    expected_cases = {case(row) for row in cases}
    raw = read(OUT/'moderators.csv')
    assert len(raw) == 1056 and len(expected_cases) == 528
    assert {(case(row), row['representation']) for row in raw} == {(c, r) for c in expected_cases for r in ['day', 'window']}
    contexts = {}
    for row in raw:
        origin = date.fromisoformat(row['origin'])
        state, year = row['state'], int(row['year'])
        family, representation = row['family'], row['representation']
        assert date.fromisoformat(row['date'])-origin == timedelta(days=int(row['horizon'])-1)
        key = state, year, origin, representation
        if key not in contexts:
            dates = [origin-timedelta(days=730-i) for i in range(730)]
            end = date(year-1, 12, 31)
            scale_days = {end-timedelta(days=i) for i in range(730)}
            scale = mean(abs(source[day][state]-source[day-timedelta(days=7)][state])
                for day in scale_days if day-timedelta(days=7) in scale_days
                and all(math.isfinite(source[t][state]) and source[t][state] > 0 for t in [day, day-timedelta(days=7)]))
            excluded = set().union(*(active[state, 'window', family] for family in FAMILIES))
            prior = [deque(maxlen=4) for _ in range(7)]
            residuals = {}
            recorded = set()
            for day in dates:
                value = source.get(day, {}).get(state, math.nan)
                if not math.isfinite(value) or value <= 0:
                    continue
                recorded.add(day)
                baseline = prior[day.weekday()]
                if len(baseline) == 4:
                    residuals[day] = (value-mean(baseline))/scale
                if day not in excluded:
                    baseline.append(value)
            means = []
            for name in FAMILIES:
                values = [value for day, value in residuals.items() if day in active[state, representation, name]]
                if values:
                    means.append(mean(values))
            heterogeneity = math.sqrt(mean((value-mean(means))**2 for value in means)) if len(means) >= 2 else math.nan
            contexts[key] = dates, recorded, scale, heterogeneity, len(means)
        dates, recorded, scale, heterogeneity, nfamilies = contexts[key]
        own = recorded&active[state, representation, family]
        pooled = recorded&set().union(*(active[state, representation, name] for name in FAMILIES))
        values = dict(own_support_days=len(own), pooled_support_days=len(pooled),
            own_support_ratio=len(own)/len(pooled) if pooled else math.nan,
            own_prior_year_support_days=sum(day.year < year for day in own),
            own_current_year_support_days=sum(day.year == year for day in own),
            heterogeneity_scaled=heterogeneity, supported_response_families=nfamilies,
            target_flag_active=int(date.fromisoformat(row['date']) in active[state, representation, family]),
            future_own_support_days=sum(origin+timedelta(days=i) in active[state, representation, family] for i in range(14)),
            recorded_context_labels=len(recorded), mase_scale=scale)
        for name, value in values.items():
            close(value, row[name])
        assert row['max_context_label'] == max(recorded).isoformat() and max(recorded) < origin
    stats = dict(status='pass', audited_utc=datetime.now(timezone.utc).isoformat(),
        scope='Separate scalar datedcalendar/recordedsupport/excludedordinaryweekdaybaseline/scaledpastresponse/heterogeneity/availability audit; no causal or independent human claim.',
        moderator_rows=len(raw), reconstructed_contexts=len(contexts), source_hash=sha(OUT/'moderators.csv'))
    if part == 'all':
        point_path = ROOT/'results/calendar_recenter_v1/analysis/breadth/event_window/predictions_compared.csv'
        run = json.loads((OUT/'run.json').read_text())
        assert sha(point_path) == run['point_source_sha256']
        assert sha(OUT/'moderators.csv') == run['moderator_source_sha256']
        predictions = {}
        with point_path.open(newline='') as stream:
            for row in csv.DictReader(stream):
                if row['version'] == 'document_aligned' and row['arm'] in ['day5', 'pooled_day5', 'window5', 'pooled_window5']:
                    key = case(row), row['model'], row['arm']
                    assert key not in predictions
                    predictions[key] = float(row['prediction']), float(row['actual']), float(row['mase_scale'])
        moderators = {(case(row), row['representation']): row for row in raw}
        paired = read(OUT/'paired_cases.csv')
        assert len(paired) == 6336
        groups = defaultdict(list)
        for row in paired:
            c, model, rep = case(row), row['model'], row['representation']
            left = predictions[c, model, rep+'5']
            right = predictions[c, model, 'pooled_'+rep+'5']
            assert left[1:] == right[1:]
            value = (abs(left[0]-left[1])-abs(right[0]-right[1]))/left[2]
            close(value, row['typed_minus_pooled_MASE'])
            for name in METRICS:
                close(float(moderators[c, rep][name]) if moderators[c, rep][name] else math.nan, row[name])
            groups[tuple(row[name] for name in ['model', 'representation', 'family', 'state', 'year', 'horizon'])].append(row)
        cells = read(OUT/'cells.csv')
        assert len(cells) == len(groups) == 864
        for row in cells:
            group = groups[tuple(row[name] for name in ['model', 'representation', 'family', 'state', 'year', 'horizon'])]
            for name in ['typed_minus_pooled_MASE']+METRICS:
                values = [float(item[name]) for item in group if item[name] != '']
                close(mean(values) if len(values) == len(group) else math.nan, row[name])
        associations = read(OUT/'associations.csv')
        assert len(associations) == 1728
        for row in associations:
            selection = [r for r in cells if all(r[k] == row[k] for k in ['model', 'representation', 'horizon'])]
            if row['scope'].startswith('year_'):
                selection = [r for r in selection if r['year'] == row['scope'][5:]]
            elif row['scope'].startswith('omit_'):
                selection = [r for r in selection if r['family'] != row['scope'][5:]]
            else:
                assert row['scope'] == 'all'
            defined = [r for r in selection if r[row['moderator']] != '' and r['typed_minus_pooled_MASE'] != '']
            x = [round(float(r[row['moderator']]), 8) for r in defined]
            y = [round(float(r['typed_minus_pooled_MASE']), 8) for r in defined]
            assert len(selection) == int(row['total_cells']) and len(defined) == int(row['defined_cells'])
            close(correlation(x, y), row['pearson'])
            close(correlation(ranks(x), ranks(y)), row['spearman'])
        stats.update(paired_cases=6336, cells=864, scalar_association_checks=1728,
                     full_point_source_sha256=sha(point_path), associations_sha256=sha(OUT/'associations.csv'))
    destination.write_text(json.dumps(stats, indent=2)+'\n')
    print(json.dumps(stats, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--part', choices=['moderators', 'all'], default='all')
    main(parser.parse_args().part)
