"""Ziel (2018) replacing variants Rph and RpH for the local models.

Section 4.5 of Ziel (2018): holiday dummies are added and "the corresponding
week-day effect is set to zero if there is a holiday" (Eq. 11). Adapted to the
five document-aligned festival families:

- `replace_pooled` (Rph): the pooled_day5 channels (one any-family day flag
  plus four zeros), with all seven weekday dummies set to 0 on flagged days.
- `replace_typed` (RpH): the day5 channels (one flag per family), with all
  seven weekday dummies set to 0 on any family anchor day.

Both have 18 channels, like every other event arm. Reference arms calendar,
day5 and pooled_day5 must reproduce the stored document-aligned forecasts.
Same cases, models, parameters, refits and metrics as results/ziel_replacing_v1,
whose registered code is reused unchanged (only its arm frames are swapped).
New versioned directory results/ziel_replacing_v2; exploratory on inspected cases.
"""
import argparse
from datetime import datetime, timezone
import json
import pandas as pd
from forecasting import ROOT
from festival_feature_design import sha, dump
from calendar_semantics_study_v2 import frames as aligned_frames
import ziel_replacing_v1 as v1

OUT = ROOT/'results/ziel_replacing_v2'
ARMS = ['calendar', 'day5', 'pooled_day5', 'replace_pooled', 'replace_typed']
REFERENCE_ARMS = ['calendar', 'day5', 'pooled_day5']
MODELS = v1.MODELS
COHORTS = v1.COHORTS
DOW = v1.DOW


def zero_weekdays(frame, flag):
    out = frame.copy()
    flag = flag.reindex(out.index).fillna(0).astype(bool)
    out.loc[flag, DOW] = 0.
    return out


def frames(index, state):
    base = aligned_frames(index, state)
    flag = base['pooled_day5']['event_day']
    typed = base['day5'].iloc[:, 13:]
    assert typed.shape[1] == 5 and bool(((typed.sum(axis=1) > 0) == flag.astype(bool)).all())
    result = {arm: base[arm] for arm in REFERENCE_ARMS}
    result['replace_pooled'] = zero_weekdays(base['pooled_day5'], flag)
    result['replace_typed'] = zero_weekdays(base['day5'], flag)
    return {arm: result[arm] for arm in ARMS}


INPUTS = v1.INPUTS + ['src/ziel_replacing_v2.py', 'src/ziel_replacing_analysis_v2.py', 'src/test_ziel_replacing_v2.py',
                      'results/ziel_replacing_v1/registration.json', 'results/ziel_replacing_v1/LABEL_CORRECTION.md']


def prepare():
    if OUT.exists():
        raise FileExistsError('Preserve the registered protocol; create a new version')
    OUT.mkdir()
    protocols = {}
    for cohort in COHORTS:
        out = OUT/cohort
        out.mkdir()
        cases = v1.cohort_cases(cohort)
        for name in ['primary_cases.csv', 'window_cases.csv']:
            cases.to_csv(out/name, index=False)
        parent = json.loads((v1.OUT/cohort/'protocol.json').read_text())
        p = dict(parent)
        p.update(
            experiment=f'{OUT.name}/{cohort}', created_utc=datetime.now(timezone.utc).isoformat(), author='Binay Verma',
            status=('Exploratory. Registered and committed before any replace_pooled or replace_typed forecast exists, on India '
                    'cases whose other arms were already inspected. Follows the label correction in results/ziel_replacing_v1.'),
            question=('Does Ziel (2018) replacing encoding (festival dummies added and weekday dummies set to zero on festival days) '
                      'change the typed-versus-pooled ordering, and how does it compare with the additive day flags, for the local models?'),
            source_method=('Ziel, F. (2018). Modeling public holidays in load forecasting: a German case study. J. Mod. Power Syst. Clean '
                           'Energy 6(2), 191-207, Section 4.5 and Eq. 11 (Rph single dummy, RpH one dummy per holiday), adapted to daily festival anchors.'),
            arms=ARMS, new_arms=['replace_pooled', 'replace_typed'], reference_arms=REFERENCE_ARMS, models=MODELS,
            new_arm_definition=('replace_pooled: pooled_day5 channels with dow_0..dow_6 = 0 on days where the any-family day flag is 1. '
                                'replace_typed: day5 channels with dow_0..dow_6 = 0 on any family anchor day. Annual harmonics unchanged. '
                                '18 channels each. Applied to training and query dates alike.'),
            contrasts=['replace_typed - replace_pooled', 'replace_pooled - pooled_day5', 'replace_typed - day5',
                       'replace_pooled - calendar', 'replace_typed - calendar'],
            input_hashes={f: sha(ROOT/f) for f in INPUTS},
            design_hashes={name: sha(out/name) for name in ['primary_cases.csv', 'window_cases.csv']},
            parent_protocol_sha256=sha(v1.OUT/cohort/'protocol.json'),
            cases_per_arm=len(cases))
        p.pop('new_arm', None)
        dump(out/'protocol.json', p)
        protocols[cohort] = sha(out/'protocol.json')
    dump(OUT/'registration.json', dict(created_utc=datetime.now(timezone.utc).isoformat(), author='Binay Verma',
        protocols=protocols, new_rows=sum(len(v1.cohort_cases(c)) for c in COHORTS)*len(MODELS)*len(ARMS),
        statement='Protocol fixed before any replace_pooled or replace_typed forecast was produced. Commit before running any worker.'))


def run(cohort, worker):
    reg = json.loads((OUT/'registration.json').read_text())
    assert sha(OUT/cohort/'protocol.json') == reg['protocols'][cohort]
    protocol = json.loads((OUT/cohort/'protocol.json').read_text())
    for f, h in protocol['input_hashes'].items():
        assert sha(ROOT/f) == h, f
    import breadth_model_engine_v1 as engine
    engine.OUT = OUT/cohort
    engine.ARMS = ARMS
    engine.EXTRA = []
    engine.frames = frames
    # Reuse the registered v1 regression unchanged; it reads these module globals.
    v1.frames = frames
    v1.ARMS = ARMS
    if worker == 'sarimax':
        engine.sarimax()
    else:
        v1.regression(engine, worker)


if __name__ == '__main__':
    a = argparse.ArgumentParser()
    a.add_argument('action', choices=['prepare', *MODELS])
    a.add_argument('--cohort', choices=COHORTS, default='event_window')
    args = a.parse_args()
    prepare() if args.action == 'prepare' else run(args.cohort, args.action)
