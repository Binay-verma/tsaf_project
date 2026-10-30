"""Fixed pooled-versus-typed follow-up; never rewrites the parent experiment."""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import json
import shutil
import numpy as np
import pandas as pd
from festival_feature_design import ROOT, OUT as PARENT, KEY, frames as parent_frames, sha, dump
import festival_feature_experiment as engine

OUT = ROOT/'results/pooled_festival_v1'
ARMS = ['pooled_day1', 'pooled_day5', 'pooled_window1', 'pooled_window5', 'zero1']
COHORTS = {'event': PARENT, 'non_event': ROOT/'results/festival_feature_spillover_v2'}


def frames(index, state):
    prior = parent_frames(index, state)
    base = prior['calendar']
    result = {}
    for kind in ['day', 'window']:
        # Logical union, not a count: coincident families remain one event day.
        flag = prior[kind+'5'].iloc[:, 13:].any(axis=1).astype(float)
        for width in [1, 5]:
            extra = pd.DataFrame({'event_'+kind: flag}, index=index)
            for k in range(1, width):
                extra['padding_'+str(k)] = 0.
            result[f'pooled_{kind}{width}'] = pd.concat([base, extra], axis=1)
    result['zero1'] = pd.concat([base, pd.DataFrame({'zero': 0.}, index=index)], axis=1)
    return result


def prepare():
    if OUT.exists():
        raise FileExistsError('Preserve existing protocol/results; version a new study')
    old = json.loads((PARENT/'protocol.json').read_text())
    paths = list(old['input_hashes']) + [
        'src/pooled_festival_experiment.py', 'src/test_pooled_festival.py',
        'results/festival_features_v1/anchors_2022_2025.csv',
        'results/festival_features_v1/placebo_anchors.csv',
        'results/festival_features_v1/protocol.json',
        'results/festival_features_v1/predictions_primary.csv',
        'results/festival_feature_spillover_v2/protocol.json',
        'results/festival_feature_spillover_v2/predictions_primary.csv']
    protected = {}
    for folder in ['data', 'results', 'evidence', 'presentation']:
        for f in (ROOT/folder).rglob('*'):
            if f.is_file() and '__pycache__' not in f.parts:
                protected[str(f.relative_to(ROOT))] = sha(f)
    OUT.mkdir(parents=True)
    dump(OUT/'protected_prior_files.json', protected)
    for name, parent in COHORTS.items():
        out = OUT/name
        out.mkdir()
        for dest in ['primary_cases.csv', 'window_cases.csv']:
            shutil.copyfile(parent/'primary_cases.csv', out/dest)
        cases = pd.read_csv(out/'primary_cases.csv')
        assert len(cases) == 72 and len(cases[['state', 'origin']].drop_duplicates()) == 72
        assert not cases.duplicated(KEY).any()
        p = dict(old)
        p.update(experiment=OUT.name+'/'+name, created_utc=datetime.now(timezone.utc).isoformat(),
            status='Exploratory historical follow-up after inspecting typed-feature results; frozen before new pooled outcomes. No clean test or external preregistration.',
            primary='The unchanged72'+name+' cases from '+str(parent.relative_to(ROOT))+'; all six model variants and all leads1/7/14. No wider-window evaluation in this follow-up.',
            secondary='No additional cohort: window_cases is an identical copy solely for the existing classical runner interface.',
            arms=ARMS, regression_extra_arms=[],
            question='Do separate family channels outperform pooled dates at the same five-channel budget? How sensitive are pooled forecasts to one versus five channels?',
            features='Pooled day/window is the logical union of the five parent state-scoped family features, in channel1. Width5 adds four exact-zero channels; width1 does not. zero1 adds one exact zero. No new dates, labels, learned encodings or target-informed features.',
            contrasts=[['day5', 'pooled_day5'], ['window5', 'pooled_window5'],
                ['pooled_day5', 'pooled_day1'], ['pooled_window5', 'pooled_window1'],
                ['pooled_day1', 'zero1'], ['pooled_window1', 'zero1'], ['zero1', 'calendar']],
            reuse='calendar/day5/window5 predictions reused byte-checked from the parent combined file; zero5/placebos retained as prior evidence, not re-fit. New pooled and zero1 arms use the identical frozen model specifications. Six variants reported separately; no model/arm selected on new errors.',
            execution_overrides='engine.OUT=cohort directory; engine.ARMS=new five arms; engine.EXTRA=[]; engine.frames=pooled constructor. Reuse original regression/annual SARIMAX/foundation engine. Both case files contain the same72cases, so no secondary-window claim.',
            interpretation='Five-channel padding controls dimension but changes information sharing/channel allocation. Typed-versus-pooled contrast is a representation comparison, not causal identification of festival identity. One or two prior typed events versus more pooled examples are intentionally different sharing assumptions. Zero padding need not be inert in foundation models.',
            limits=old['limits'][:-1]+['Both cohorts inspected historically; secondary controls are bounded, not all-day operational validation',
                'No untouched/prospective, external human review, source permission or independent-source claim',
                'No future-outcome retrieval or modification of frozen forecasts/automation'],
            input_hashes={f: sha(ROOT/f) for f in paths},
            design_hashes={f: sha(out/f) for f in ['primary_cases.csv', 'window_cases.csv']},
            parent_combined_sha256=sha(parent/'predictions_primary.csv'),
            protection_manifest_sha256=sha(OUT/'protected_prior_files.json'))
        dump(out/'protocol.json', p)
    dump(OUT/'registration.json', dict(created_utc=datetime.now(timezone.utc).isoformat(),
        cohorts=list(COHORTS), new_arms=ARMS, cases_per_arm_cohort=72,
        new_rows_planned=2*6*5*72, protocols={k: sha(OUT/k/'protocol.json') for k in COHORTS},
        note='Recorded before any new pooled fits/inference; prior typed outcomes already inspected.'))
    print('FROZEN: 2 cohorts x 6 variants x 5 new arms x 72 cases = 4320 new rows')


def run(cohort, worker):
    registration = json.loads((OUT/'registration.json').read_text())
    out = OUT/cohort
    assert sha(out/'protocol.json') == registration['protocols'][cohort]
    engine.OUT = out
    engine.ARMS = ARMS
    engine.EXTRA = []
    engine.frames = frames
    if worker in ['chronos', 'timesfm']:
        engine.foundation(worker)
    elif worker == 'sarimax':
        engine.sarimax()
    else:
        engine.regression(worker)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['prepare', 'ridge', 'lightgbm', 'lightgbm_capacity2', 'sarimax', 'chronos', 'timesfm'])
    parser.add_argument('--cohort', choices=list(COHORTS), default='event')
    args = parser.parse_args()
    prepare() if args.action == 'prepare' else run(args.cohort, args.action)
