"""Ziel (2018) replacing ("holiday-as-Sunday") comparator for the local models.

Exploratory study on already-inspected India cases. New versioned directory
results/ziel_replacing_v1; no earlier file is edited. The protocol is written
and committed before any forecast of the new arm exists.

New arm `sunday_day`: the 13 ordinary calendar channels, except that on every
document-aligned festival anchor date (any of the five families, the same dates
that switch on `pooled_day5`) the weekday one-hot is replaced by the Sunday
one-hot (dow_6 = 1, dow_0..dow_5 = 0). No additive festival indicator is added.
Five zero channels keep the channel count equal to the other event arms (18).

Reference arms `calendar`, `day5` and `pooled_day5` are recomputed with the same
code and must reproduce the stored document-aligned forecasts.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import time
import traceback
import numpy as np
import pandas as pd
from forecasting import ROOT
from festival_feature_design import sha, dump
from calendar_semantics_study_v2 import frames as aligned_frames

OUT = ROOT/'results/ziel_replacing_v1'
ARMS = ['calendar', 'day5', 'pooled_day5', 'sunday_day']
REFERENCE_ARMS = ['calendar', 'day5', 'pooled_day5']
MODELS = ['ridge', 'lightgbm', 'lightgbm_capacity2', 'sarimax']
COHORTS = ['event_window', 'ordinary']
CASE_COLUMNS = ['family', 'state', 'year', 'date', 'horizon', 'origin']
DOW = [f'dow_{i}' for i in range(7)]
COMPOSED = ROOT/'results/calendar_recenter_recovery_v1/analysis/breadth'


def replace_with_sunday(calendar, flag):
    """Ziel's replacing rule on a 13-channel calendar frame: weekday -> Sunday on flagged days."""
    out = calendar.copy()
    flag = flag.reindex(out.index).fillna(0).astype(bool)
    out.loc[flag, DOW] = 0.
    out.loc[flag, 'dow_6'] = 1.
    return out


def frames(index, state):
    base = aligned_frames(index, state)
    result = {arm: base[arm] for arm in REFERENCE_ARMS}
    calendar = base['calendar']
    assert list(calendar.columns[:7]) == DOW and calendar.shape[1] == 13
    flag = base['pooled_day5']['event_day']
    sunday = replace_with_sunday(calendar, flag)
    for j in range(1, 6):
        sunday[f'padding_{j}'] = 0.
    result['sunday_day'] = sunday
    return {arm: result[arm] for arm in ARMS}


def cohort_cases(cohort):
    d = pd.read_csv(COMPOSED/cohort/'predictions_compared.csv')
    d = d[d.version.eq('document_aligned') & d.model.eq('ridge') & d.arm.eq('calendar')]
    cases = d[CASE_COLUMNS].drop_duplicates().sort_values(['state', 'origin', 'horizon']).reset_index(drop=True)
    assert len(cases) == (528 if cohort == 'event_window' else 216)
    return cases


INPUTS = ['src/ziel_replacing_v1.py', 'src/ziel_replacing_analysis_v1.py', 'src/test_ziel_replacing_v1.py',
          'src/breadth_model_engine_v1.py', 'src/calendar_semantics_study_v2.py', 'src/breadth_study.py',
          'src/festival_feature_design.py', 'src/pooled_festival_experiment.py', 'src/robust_baselines.py',
          'src/forecasting.py', 'src/extended_validation.py', 'src/multifestival_models.py',
          'data/external/latest_state_energy_GWh.csv', 'results/calendar_semantics_v2/anchors_2022_2025.csv',
          'results/strong_refit_v1/selected.csv', 'results/stable_tree_refit_v2/selected.csv',
          'results/strong_refit_v1/protocol.json', 'results/stable_tree_refit_v2/protocol.json',
          'results/strong_refit_v1/predictions.csv',
          'results/calendar_recenter_recovery_v1/analysis/breadth/event_window/predictions_compared.csv',
          'results/calendar_recenter_recovery_v1/analysis/breadth/ordinary/predictions_compared.csv']


def prepare():
    if OUT.exists():
        raise FileExistsError('Preserve the registered protocol; create a new version')
    OUT.mkdir()
    protocols = {}
    for cohort in COHORTS:
        out = OUT/cohort
        out.mkdir()
        cases = cohort_cases(cohort)
        for name in ['primary_cases.csv', 'window_cases.csv']:
            cases.to_csv(out/name, index=False)
        p = dict(
            experiment=f'{OUT.name}/{cohort}', created_utc=datetime.now(timezone.utc).isoformat(), author='Binay Verma',
            status=('Exploratory. Registered and committed before any sunday_day forecast exists, but on India cases whose '
                    'other arms were already inspected. Not a confirmation and not a preregistration in the external sense.'),
            question=('Does Ziel (2018) replacing encoding (festival day treated as Sunday, no additive indicator) differ from '
                      'the additive pooled and typed day indicators for the local models on the same cases?'),
            source_method='Ziel, F. (2018). Modeling public holidays in load forecasting: a German case study. Journal of Modern Power Systems and Clean Energy 6(2), 191-207. Replacing holiday-as-Sunday variant, adapted to daily festival anchors.',
            arms=ARMS, new_arm='sunday_day', reference_arms=REFERENCE_ARMS, models=MODELS,
            new_arm_definition=('13 calendar channels; on every document-aligned anchor date of any of the five families '
                                '(identical dates to pooled_day5 event_day) dow_0..dow_5 = 0 and dow_6 = 1; plus five zero '
                                'channels (18 channels, equal to the other event arms). Applied to training and query dates alike.'),
            local_design=('Ridge/LightGBM: the registered rich-history design; its 13 calendar columns are replaced in place by the '
                          'arm frame at the target date, then the arm extra channels are appended. Reference arms therefore '
                          'reproduce the parent matrix exactly. SARIMAX(1,0,0)(1,0,0,7): the whole 18- or 13-channel arm frame is the exogenous input.'),
            selection='No search. Reuse the stored past-selected parameters (strong_refit_v1, stable_tree_refit_v2) unchanged; capacity2 override min_child_samples=2 as before. Monthly refits as in the parent engine.',
            cases=('event_window: the 528 composed document-aligned window cases (176 state-dates x leads 1, 7, 14). '
                   'ordinary: the 216 composed ordinary cases. Taken from the composed analysis files listed in input_hashes.'),
            reproduction_check='Reference-arm predictions must match the stored document_aligned predictions for the same model, arm and case within atol 1e-7 GWh, rtol 1e-9. Any mismatch is reported as a failure and the new arm is not interpreted.',
            metrics=('Row MASE = |prediction - actual| / fixed pre-year 730-day weekly scale. Balanced event MASE = mean over families of '
                     'mean over years of mean over states of mean row MASE (the v6 hierarchy). Ordinary cohort: mean over years of mean over states.'),
            contrasts=['sunday_day - pooled_day5', 'sunday_day - day5', 'sunday_day - calendar'],
            reporting=('Leads 1, 7 and 14 for every model. For each contrast: balanced value, family-year cluster signs, '
                       'leave-one-family-out range and sign flips, and 2024 versus 2025 values. Ordinary-cohort cost of each arm '
                       'versus calendar. No p-values, no bootstrap, no winner selection; negative and null results are reported.'),
            interpretation=('A contrast is described as consistent only if its sign holds in both years and in every leave-one-family-out '
                            'subset; otherwise it is described as unstable. Values with absolute size below 0.005 MASE are called negligible.'),
            input_hashes={f: sha(ROOT/f) for f in INPUTS},
            design_hashes={name: sha(out/name) for name in ['primary_cases.csv', 'window_cases.csv']},
            cases_per_arm=len(cases))
        dump(out/'protocol.json', p)
        protocols[cohort] = sha(out/'protocol.json')
    dump(OUT/'registration.json', dict(created_utc=datetime.now(timezone.utc).isoformat(), author='Binay Verma',
        protocols=protocols, new_rows=sum(len(cohort_cases(c)) for c in COHORTS)*len(MODELS)*len(ARMS),
        statement='Protocol fixed before any sunday_day forecast was produced. Commit this registration before running any worker.'))


def regression(engine, worker):
    """Parent engine regression with in-place calendar replacement (identical for reference arms)."""
    from robust_baselines import design_frame, fitting_cases, make_model
    p, out, cases, data = engine.setup(worker)
    model_name = 'ridge' if worker == 'ridge' else 'lightgbm'
    old = 'strong_refit_v1' if model_name == 'ridge' else 'stable_tree_refit_v2'
    selected = pd.read_csv(ROOT/f'results/{old}/selected.csv')
    fixed = json.loads((ROOT/f'results/{old}/protocol.json').read_text())
    rows, fits = [], []
    started = time.perf_counter()
    try:
        for (state, year, horizon), group in cases.groupby(['state', 'year', 'horizon']):
            observed = data[state]
            fc = frames(data.index, state)
            base, _ = design_frame(observed, state, int(horizon), 'rich_calendar')
            calendar_columns = list(fc['calendar'].columns)
            chosen = selected[selected.state.eq(state) & selected.year.eq(year) & selected.horizon.eq(horizon)
                              & selected['mode'].eq('rich_calendar') & selected.model.eq(model_name)]
            assert len(chosen) == 1
            params = json.loads(chosen.parameters.iloc[0])
            if worker == 'lightgbm_capacity2':
                params['min_child_samples'] = 2
            for arm in ARMS:
                shifted = fc[arm].reindex(data.index+pd.Timedelta(days=int(horizon)-1)).copy()
                shifted.index = data.index
                x = base.copy()
                x[calendar_columns] = shifted.iloc[:, :13].to_numpy()
                x = pd.concat([x, shifted.iloc[:, 13:]], axis=1)
                if model_name == 'lightgbm':
                    x = x.astype(np.float32)
                chunks = []
                for month, segment in group.groupby(group.origin.dt.to_period('M')):
                    refit = pd.Timestamp(month.start_time)
                    cutoff = refit-pd.Timedelta(days=1)
                    first = cutoff-pd.Timedelta(days=729)+pd.Timedelta(days=int(horizon)-1)
                    engine.ledger_bound([first, cutoff, segment.date.min(), segment.date.max()])
                    xx, yy, log = fitting_cases(x, observed, int(horizon), cutoff)
                    assert pd.Timestamp(log['training_target_max']) < refit <= segment.origin.min()
                    query = x.reindex(pd.DatetimeIndex(segment.origin)).to_numpy()
                    model = make_model(model_name, params, fixed).fit(xx, yy)
                    a = segment.copy()
                    a['prediction'] = model.predict(query)
                    a['mase_scale'] = engine.scale(data, state, int(year))
                    a['model'] = worker
                    a['arm'] = arm
                    chunks.append(a)
                    replaced = int(np.count_nonzero(xx[:, list(x.columns).index('dow_6')]))
                    fits.append(dict(model=worker, arm=arm, state=state, year=int(year), horizon=int(horizon),
                        refit=str(refit.date()), parameters=params, feature_count=xx.shape[1],
                        training_dow6_rows=replaced,
                        training_X_sha256=hashlib.sha256(xx.tobytes()).hexdigest(),
                        training_y_sha256=hashlib.sha256(yy.tobytes()).hexdigest(),
                        query_X_sha256=hashlib.sha256(query.tobytes()).hexdigest(), **log))
                rows.append(pd.concat(chunks, ignore_index=True))
                pd.concat(rows, ignore_index=True).to_csv(out/'checkpoint.csv', index=False)
                dump(out/'fit_log.json', fits)
            print(worker, state, year, horizon, 'complete', flush=True)
        d = pd.concat(rows, ignore_index=True)
        assert len(d) == len(cases)*len(ARMS) and np.isfinite(d.prediction).all()
        d.to_csv(out/'predictions.csv', index=False)
        dump(out/'run.json', dict(model=worker, completed_utc=datetime.now(timezone.utc).isoformat(), fits=len(fits),
            rows=len(d), cases_per_arm=len(cases), arms=ARMS, seconds=time.perf_counter()-started,
            predictions_sha256=sha(out/'predictions.csv'), protocol_sha256=sha(engine.OUT/'protocol.json')))
    except Exception:
        (out/'failure.txt').write_text(traceback.format_exc())
        dump(out/'fit_log.json', fits)
        raise


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
    if worker == 'sarimax':
        engine.sarimax()
    else:
        regression(engine, worker)


if __name__ == '__main__':
    a = argparse.ArgumentParser()
    a.add_argument('action', choices=['prepare', *MODELS])
    a.add_argument('--cohort', choices=COHORTS, default='event_window')
    args = a.parse_args()
    prepare() if args.action == 'prepare' else run(args.cohort, args.action)
