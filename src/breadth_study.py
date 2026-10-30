"""Registered full-window/seasonally spread control extension; no old outputs edited."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import pandas as pd
from festival_feature_design import ROOT, KEY, sha, dump, frames as typed_frames
from pooled_festival_experiment import frames as pooled_frames

OUT = ROOT/'results/feature_breadth_v1'
ARMS = ['calendar', 'zero5', 'day5', 'pooled_day5', 'window5',
        'pooled_window5', 'placebo_day5', 'placebo_window5']
MODELS = ['ridge', 'lightgbm', 'lightgbm_capacity2', 'sarimax', 'chronos', 'timesfm']


def frames(index, state):
    all_frames = {**typed_frames(index, state), **pooled_frames(index, state)}
    return {arm: all_frames[arm] for arm in ARMS}


def ordinary_cases():
    annual = pd.read_csv(ROOT/'results/extended_validation/regional_calendar_date_audit.csv')
    named = pd.read_csv(ROOT/'results/festival_features_v1/anchors_2022_2025.csv')
    rows = []
    for state in ['Delhi', 'Karnataka', 'Maharashtra']:
        for year in [2024, 2025]:
            annual_dates = annual[annual.state.eq(state) & annual.year.eq(year) & annual.in_annual_schedule].date
            named_dates = named[named.state.eq(state) & named.year.eq(year)].date
            blocked = {d for a in pd.to_datetime(list(annual_dates)+list(named_dates))
                       for d in pd.date_range(a-pd.Timedelta(days=3), a+pd.Timedelta(days=3))}
            for month in range(1, 13):
                weekday = (month-1+3*(year-2024)) % 7
                possible = [d for d in pd.date_range(f'{year}-{month:02d}-01', periods=31)
                            if d.month == month and d.weekday() == weekday and d not in blocked
                            and pd.Timestamp(f'{year}-01-14') <= d <= pd.Timestamp(f'{year}-12-18')]
                if not possible:
                    raise ValueError(('No calendar-only ordinary candidate', state, year, month, weekday))
                date = possible[0]
                for horizon in [1, 7, 14]:
                    rows.append(dict(family='Ordinary', state=state, year=year, date=str(date.date()),
                        origin=str((date-pd.Timedelta(days=horizon-1)).date()), horizon=horizon,
                        month=month, requested_weekday=weekday))
    result = pd.DataFrame(rows).sort_values(KEY)
    assert len(result) == 216 and not result.duplicated(KEY).any()
    return result


def prepare():
    if OUT.exists():
        raise FileExistsError('Preserve prior protocol/output; create a new version')
    ordinary = ordinary_cases()  # feasibility uses dates only, before directory/protocol creation
    parent = ROOT/'results/festival_features_v1'
    old = json.loads((parent/'protocol.json').read_text())
    paths = list(old['input_hashes']) + ['src/breadth_study.py', 'src/breadth_model_engine_v1.py',
        'src/test_breadth_study.py', 'src/pooled_festival_experiment.py',
        'results/festival_features_v1/anchors_2022_2025.csv',
        'results/festival_features_v1/placebo_anchors.csv',
        'results/festival_features_v1/window_cases.csv',
        'results/strong_refit_v1/predictions.csv', 'results/stable_tree_refit_v2/predictions.csv']
    protected = {}
    for folder in ['data', 'results', 'evidence', 'presentation', 'manuscript', 'review']:
        for f in (ROOT/folder).rglob('*'):
            if f.is_file() and '__pycache__' not in f.parts:
                protected[str(f.relative_to(ROOT))] = sha(f)
    OUT.mkdir()
    dump(OUT/'protected_prior_files.json', protected)
    protocols = {}
    for cohort in ['event_window', 'ordinary']:
        out = OUT/cohort
        out.mkdir()
        cases = pd.read_csv(parent/'window_cases.csv') if cohort == 'event_window' else ordinary
        for dest in ['primary_cases.csv', 'window_cases.csv']:
            cases.to_csv(out/dest, index=False)
        tasks = len(cases[['state', 'origin']].drop_duplicates())
        p = dict(old)
        p.update(experiment=f'{OUT.name}/{cohort}', created_utc=datetime.now(timezone.utc).isoformat(),
            status='Exploratory extension registered before new breadth outputs, after historical anchor/pooled results were examined. No untouched or external preregistration claim.',
            question='Do sparse typed-versus-pooled feature effects persist across complete festival windows, and what costs occur on a seasonal ordinary-day sample?',
            primary='Same528parent event-window cases for ALL six variants and eight arms, not just anchor targets. Equal states within year, years within family, families overall.',
            secondary='216ordinary cases:12target dates/state/year, three leads. First eligible requested weekday in each month; weekday=(month-1+3*(year-2024))mod7. Exclude+/-3days around every annual-as-issued and named holiday. Targets14January–18December keep every730+14context within2022–2025. No target magnitude/error selects dates. This is a seasonally spread bounded sample, not all daily cases.',
            cohort=cohort, arms=ARMS, regression_extra_arms=[], expected_tasks=tasks,
            cases_per_arm=len(cases), batch=16, threads=2,
            features='Same frozen parent named dates and placebo shifts. Typed5 versus pooled5 has equal18totalchannels (13calendar+5event); pooled5=unionflag+4zeros. Calendar13 and zero5 are dimension controls. Both day/window and active placebos retained; no arm selected using new errors. One-vs-five padding is already separately tested and is not rerun here.',
            foundation_models='Same pinned weights and inference settings as parent except batch16 to amortise wider-panel overhead;2threads/seed42/730context/14leads. First batch everyarm checked against solo forecasts. Native quantiles retained unchanged. Actual-input hashes and future-target perturbation every task.',
            execution_overrides='Versioned derived engine copies parent logic, removes72-task restriction using protocol expected_tasks, and checks local calendar predictions against original full-daily references. Both case files identical; all6models run all8arms fresh. No parent output reused or overwritten. No hyperparameter search.',
            limits=[*old['limits'][:-1], 'Ordinary monthly targets are not independent replications or exhaustive all-day coverage',
                'Two historical event years; all outcomes remain exploratory',
                'No source permission, external human review, new future outcome or automation change'],
            input_hashes={f: sha(ROOT/f) for f in paths},
            design_hashes={f: sha(out/f) for f in ['primary_cases.csv', 'window_cases.csv']},
            protection_manifest_sha256=sha(OUT/'protected_prior_files.json'))
        dump(out/'protocol.json', p)
        protocols[cohort] = sha(out/'protocol.json')
    dump(OUT/'registration.json', dict(created_utc=datetime.now(timezone.utc).isoformat(),
        cohorts=protocols, models=MODELS, arms=ARMS, planned_rows=6*8*(528+216),
        primary_contrasts=[['day5','pooled_day5'], ['window5','pooled_window5']],
        control_contrasts=[['day5','zero5'], ['window5','zero5'], ['day5','placebo_day5'],
                           ['window5','placebo_window5'], ['pooled_day5','zero5'], ['pooled_window5','zero5']],
        inference='Descriptive paired event/state/year cells and both-year/leave-family-out sensitivity. No independent-row significance tests or bootstrap claim of many independent years.',
        note='No new model outputs existed when this registration was created. Future freezes untouched.'))
    print('FROZEN: 528window+216ordinary cases x8arms x6variants =35712rows', flush=True)


def run(cohort, worker):
    import breadth_model_engine_v1 as engine
    registration = json.loads((OUT/'registration.json').read_text())
    out = OUT/cohort
    assert sha(out/'protocol.json') == registration['cohorts'][cohort]
    engine.OUT, engine.ARMS, engine.EXTRA, engine.frames = out, ARMS, [], frames
    if worker in ['chronos', 'timesfm']:
        engine.foundation(worker)
    elif worker == 'sarimax':
        engine.sarimax()
    else:
        engine.regression(worker)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['prepare', *MODELS])
    parser.add_argument('--cohort', choices=['event_window', 'ordinary'], default='event_window')
    args = parser.parse_args()
    prepare() if args.action == 'prepare' else run(args.cohort, args.action)
