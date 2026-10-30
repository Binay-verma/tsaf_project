"""Prespecified matched non-event secondary cohort; same frozen model rules."""
import argparse
from datetime import datetime, timezone
import json
import numpy as np
import pandas as pd
import festival_feature_experiment as experiment
from festival_feature_design import ROOT, OUT as PARENT, KEY, sha, dump

OUT = ROOT/'results/festival_feature_spillover_v1'
ARMS = ['calendar', 'day5', 'window5']


def prepare():
    if OUT.exists():
        raise FileExistsError('Preserve secondary design')
    anchors = pd.read_csv(PARENT/'primary_cases.csv')
    calendar = pd.read_csv(ROOT/'results/extended_validation/regional_calendar_date_audit.csv')
    registered = pd.read_csv(PARENT/'anchors_2022_2025.csv')
    # Select dates with no target/forecast-error information. Every family/state/
    # year keeps its three lead cases and a shared weekday-preserving shift.
    rows, choices = [], []
    for (family, state, year), group in anchors.groupby(['family', 'state', 'year']):
        target = pd.Timestamp(group.date.iloc[0])
        assert group.date.nunique() == 1
        dates = pd.to_datetime(calendar[calendar.state.eq(state) & calendar.year.eq(year) & calendar.in_annual_schedule].date)
        dates = list(dates)+list(pd.to_datetime(registered[registered.state.eq(state) & registered.year.eq(year)].date))
        blocked = {d for a in dates for d in pd.date_range(a-pd.Timedelta(days=3), a+pd.Timedelta(days=3))}
        possible = [k for k in [28, -28, 35, -35, 42, -42] if (target+pd.Timedelta(days=k)).year == year and (target+pd.Timedelta(days=k)) not in blocked]
        assert possible, (family, state, year)
        shift = possible[0]
        for r in group.itertuples(index=False):
            date = pd.Timestamp(r.date)+pd.Timedelta(days=shift)
            origin = date-pd.Timedelta(days=r.horizon-1)
            rows.append(dict(family=family, state=state, year=int(year), origin=str(origin.date()),
                date=str(date.date()), horizon=int(r.horizon), matched_event_date=r.date, shift_days=shift))
        choices.append(dict(family=family, state=state, year=int(year), event_date=str(target.date()),
            non_event_date=str((target+pd.Timedelta(days=shift)).date()), shift_days=shift))
    d = pd.DataFrame(rows).sort_values(KEY)
    assert len(d) == 72 and not d.duplicated(KEY).any()
    assert len(d[['state', 'origin']].drop_duplicates()) == 72
    OUT.mkdir(parents=True)
    d.to_csv(OUT/'primary_cases.csv', index=False)
    d.to_csv(OUT/'window_cases.csv', index=False)
    pd.DataFrame(choices).to_csv(OUT/'date_only_matching.csv', index=False)
    for f in ['anchors_2022_2025.csv', 'placebo_anchors.csv']:
        (OUT/f).write_bytes((PARENT/f).read_bytes())
    p = json.loads((PARENT/'protocol.json').read_text())
    p.update(experiment=OUT.name, created_utc=datetime.now(timezone.utc).isoformat(),
        status='Secondary spillover protocol frozen before non-event model outputs; primary event experiment already started. Historical benchmarks inspected; still exploratory.',
        primary='72weekday-matched non-event cases; select first eligible shift from+28,-28,+35,-35,+42,-42days, excluding+/-3days of every annual schedule/registered family anchor in the same state/year. Same cases/arms for all6model variants. No errors or target magnitudes select dates.',
        secondary='Bounded seasonal/weekday-matched spillover diagnostic, not an all-day or operational evaluation. Event-family label denotes the matched pair, not a festival observed on control date.',
        arms=ARMS, regression_extra_arms=[],
        execution_overrides='Wrapper explicitly sets experiment.OUT to this directory, experiment.ARMS to calendar/day5/window5 and experiment.EXTRA empty. Date-feature frames continue to use parent frozen true/placebo ledger. No model/feature code or parent forecasts overwritten.',
        cases_sha256=sha(OUT/'primary_cases.csv'))
    p['input_hashes']['src/festival_feature_spillover.py'] = sha(Path(__file__))
    p['input_hashes']['results/festival_features_v1/protocol.json'] = sha(PARENT/'protocol.json')
    p['design_hashes'] = {f: sha(OUT/f) for f in ['primary_cases.csv', 'window_cases.csv', 'anchors_2022_2025.csv', 'placebo_anchors.csv', 'date_only_matching.csv']}
    dump(OUT/'protocol.json', p)
    print('FROZEN72matched non-event cases;3arms;6model variants; date-only matching')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['prepare', 'ridge', 'lightgbm', 'lightgbm_capacity2', 'sarimax', 'chronos', 'timesfm'])
    action = parser.parse_args().action
    if action == 'prepare':
        prepare()
    else:
        experiment.OUT = OUT
        experiment.ARMS = ARMS
        experiment.EXTRA = []
        if action in ['chronos', 'timesfm']:
            experiment.foundation(action)
        elif action == 'sarimax':
            experiment.sarimax()
        else:
            experiment.regression(action)
