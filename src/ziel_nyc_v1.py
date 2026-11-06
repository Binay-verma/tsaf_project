"""Ziel (2018) hSun and replacing (Rph, RpH) comparators on the NYC MTA replication.

Same cases, source snapshot, past-only selected parameters, monthly refits,
seven-day observation buffer and SARIMAX policy as results/mta_holiday_v1
(local models only). Exploratory: the NYC calendar/typed/pooled arms were
already inspected. New versioned directory results/ziel_nyc_v1.

Arms (13 ordinary calendar channels first, as in the parent):
- calendar, day5, pooled_day5: reference arms, must reproduce the parent forecasts.
- sunday_day (hSun): weekday one-hot replaced by Sunday on any family anchor day, plus five zeros.
- replace_pooled (Rph): pooled_day5 with all weekday dummies set to 0 on flagged days.
- replace_typed (RpH): day5 with all weekday dummies set to 0 on any family anchor day.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import time
import traceback
import numpy as np
import pandas as pd
from forecasting import ROOT, causal_fill
from festival_feature_design import sha, dump
import mta_holiday_study as mta
from ziel_replacing_v1 import replace_with_sunday, DOW
from ziel_replacing_v2 import zero_weekdays

OUT = ROOT/'results/ziel_nyc_v1'
PARENT = ROOT/'results/mta_holiday_v1'
ARMS = ['calendar', 'day5', 'pooled_day5', 'sunday_day', 'replace_pooled', 'replace_typed']
REFERENCE_ARMS = ['calendar', 'day5', 'pooled_day5']
MODELS = ['ridge', 'lightgbm', 'lightgbm_capacity2', 'sarimax']
COHORTS = ['event_window', 'ordinary']


def frames(index, state=None):
    base = mta.frames(index, state)
    flag = base['pooled_day5']['event_day']
    result = {arm: base[arm] for arm in REFERENCE_ARMS}
    sunday = replace_with_sunday(base['calendar'], flag)
    for j in range(1, 6):
        sunday[f'padding_{j}'] = 0.
    result['sunday_day'] = sunday
    result['replace_pooled'] = zero_weekdays(base['pooled_day5'], flag)
    result['replace_typed'] = zero_weekdays(base['day5'], flag)
    return {arm: result[arm] for arm in ARMS}


def design(observed, h, arm):
    from robust_baselines import rich_history
    index = pd.date_range(observed.index.min(), observed.index.max()+pd.Timedelta(days=20))
    f = frames(index)[arm].reindex(observed.index+pd.Timedelta(days=h-1)).copy()
    f.index = observed.index
    return pd.concat([rich_history(observed, h), f], axis=1)


INPUTS = ['src/ziel_nyc_v1.py', 'src/ziel_nyc_analysis_v1.py', 'src/test_ziel_nyc_v1.py', 'src/ziel_replacing_v1.py',
          'src/ziel_replacing_v2.py', 'src/mta_holiday_study.py', 'src/mta_model_engine_v1.py', 'src/robust_baselines.py',
          'src/multifestival_models.py', 'src/forecasting.py', 'results/mta_holiday_v1/anchors.csv',
          'results/mta_holiday_v1/snapshot.json', 'results/mta_holiday_v1/source_records.json',
          'results/mta_holiday_v1/source_snapshot_million_rides.csv', 'results/mta_holiday_v1/selection.json',
          'results/mta_holiday_v1/event_window/protocol.json', 'results/mta_holiday_v1/ordinary/protocol.json',
          'results/mta_holiday_recovery_v1/analysis/event_window/predictions_compared.csv',
          'results/mta_holiday_recovery_v1/analysis/ordinary/predictions_compared.csv',
          'results/ziel_replacing_v1/LABEL_CORRECTION.md']


def prepare():
    if OUT.exists():
        raise FileExistsError('Preserve the registered protocol; create a new version')
    OUT.mkdir()
    protocols = {}
    for cohort in COHORTS:
        out = OUT/cohort
        out.mkdir()
        for name in ['primary_cases.csv', 'window_cases.csv']:
            (out/name).write_bytes((PARENT/cohort/name).read_bytes())
        parent = json.loads((PARENT/cohort/'protocol.json').read_text())
        p = dict(experiment=f'{OUT.name}/{cohort}', created_utc=datetime.now(timezone.utc).isoformat(), author='Binay Verma',
            status=('Exploratory. Registered and committed before any sunday_day, replace_pooled or replace_typed NYC forecast exists. '
                    'The NYC calendar, typed and pooled arms were already inspected. Not a confirmation.'),
            question='Do the Ziel (2018) hSun and replacing encodings change the local-model ordering on the separate NYC holiday cases?',
            source_method='Ziel (2018) J. Mod. Power Syst. Clean Energy 6(2), 191-207: Section 4.3 hSun and Section 4.5 replacing (Rph, RpH, Eq. 11), adapted to daily observance anchors.',
            arms=ARMS, new_arms=['sunday_day', 'replace_pooled', 'replace_typed'], reference_arms=REFERENCE_ARMS, models=MODELS,
            new_arm_definition=('sunday_day: calendar with weekday one-hot replaced by dow_6 on any family anchor day, plus five zeros. '
                                'replace_pooled: pooled_day5 with dow_0..dow_6 = 0 on flagged days. replace_typed: day5 with dow_0..dow_6 = 0 '
                                'on any family anchor day. 18 channels each; training and query dates alike.'),
            parent_rules=dict(cases=parent['cases'], availability=parent['availability'], selection=parent['selection'],
                              local=parent['local'], metrics=parent['metrics']),
            reproduction_check='Reference-arm predictions must match results/mta_holiday_v1 local predictions within atol 1e-7, rtol 1e-9, and the stored balanced MASE within 1e-12. Otherwise the new arms are not interpreted.',
            metrics=('Row MASE = |prediction - actual| / fixed 2024-01-02..2025-12-31 weekly scale. Balanced MASE = mean over families of the '
                     'mean over (mode, year) cells (the parent aggregate). Model steps 8/14/21 = decision leads 1/7/14.'),
            contrasts=['sunday_day - pooled_day5', 'replace_pooled - pooled_day5', 'replace_typed - day5', 'replace_typed - replace_pooled',
                       'sunday_day - calendar', 'replace_pooled - calendar', 'replace_typed - calendar'],
            reporting=('Every model, contrast and lead: balanced value, value per mode, leave-one-family-out values, and family/mode cell signs. '
                       'No p-values or bootstrap. Two observances and two related modes: a bounded robustness check only.'),
            interpretation=('Consistent only if the sign holds in both modes and in both leave-one-family-out subsets; values below 0.005 MASE '
                            'in absolute size are negligible; otherwise unstable.'),
            input_hashes={f: sha(ROOT/f) for f in INPUTS},
            design_hashes={name: sha(out/name) for name in ['primary_cases.csv', 'window_cases.csv']},
            parent_protocol_sha256=sha(PARENT/cohort/'protocol.json'))
        dump(out/'protocol.json', p)
        protocols[cohort] = sha(out/'protocol.json')
    dump(OUT/'registration.json', dict(created_utc=datetime.now(timezone.utc).isoformat(), author='Binay Verma', protocols=protocols,
        statement='Protocol fixed before any new-arm NYC forecast was produced. Commit before running any worker.'))


def regression(engine, cohort, worker):
    from robust_baselines import fitting_cases, make_model
    p, out, cases, data = engine.setup(worker)
    selected = json.loads((PARENT/'selection.json').read_text())['parameters']
    fixed = json.loads((PARENT/cohort/'protocol.json').read_text())
    model = 'ridge' if worker == 'ridge' else 'lightgbm'
    rows, fits = [], []
    try:
        for (state, h), group in cases.groupby(['state', 'horizon']):
            observed = data[state]
            params = selected[f'{state}:{model}:{int(h)}'].copy()
            if worker == 'lightgbm_capacity2':
                params['min_child_samples'] = 2
            for arm in ARMS:
                x = design(observed, int(h), arm)
                x = x.astype(np.float32) if model == 'lightgbm' else x
                for month, g in group.groupby(group.origin.dt.to_period('M')):
                    cutoff = pd.Timestamp(month.start_time)-pd.Timedelta(days=1)
                    xx, yy, log = fitting_cases(x, observed, int(h), cutoff)
                    query = x.reindex(pd.DatetimeIndex(g.origin)).to_numpy()
                    pred = make_model(model, params, fixed).fit(xx, yy).predict(query)
                    assert pd.Timestamp(log['training_target_max']) <= cutoff < g.origin.min()
                    a = g.copy(); a['prediction'] = pred
                    a['actual'] = observed.reindex(pd.DatetimeIndex(g.date)).to_numpy()
                    a['mase_scale'] = engine.scale(data, state, 2026); a['model'] = worker; a['arm'] = arm
                    rows.append(a)
                    fits.append(dict(state=state, horizon=int(h), arm=arm, refit=str((cutoff+pd.Timedelta(days=1)).date()),
                        parameters=params, feature_count=xx.shape[1], training_X_sha256=hashlib.sha256(xx.tobytes()).hexdigest(),
                        training_y_sha256=hashlib.sha256(yy.tobytes()).hexdigest(),
                        query_X_sha256=hashlib.sha256(query.tobytes()).hexdigest(), **log))
                pd.concat(rows).to_csv(out/'checkpoint.csv', index=False); dump(out/'fit_log.json', fits)
        d = pd.concat(rows)
        assert len(d) == len(cases)*len(ARMS) and np.isfinite(d.prediction).all()
        d.to_csv(out/'predictions.csv', index=False)
        dump(out/'run.json', dict(model=worker, completed_utc=datetime.now(timezone.utc).isoformat(), rows=len(d), fits=len(fits),
            arms=ARMS, predictions_sha256=sha(out/'predictions.csv'), protocol_sha256=sha(OUT/cohort/'protocol.json')))
    except BaseException:
        (out/'failure.txt').write_text(traceback.format_exc()); dump(out/'fit_log.json', fits); raise


def sarimax(engine, cohort):
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    from multifestival_models import fit_checked
    p, out, cases, data = engine.setup('sarimax')
    rows, attempts, updates = [], [], []
    fc = frames(pd.date_range(data.index.min(), data.index.max()+pd.Timedelta(days=20)))
    try:
        for state, gstate in cases.groupby('state'):
            observed = data[state]; y = causal_fill(observed)
            for month, group in gstate.groupby(gstate.origin.dt.to_period('M')):
                cutoff = pd.Timestamp(month.start_time)-pd.Timedelta(days=1)
                tr = y.loc[cutoff-pd.Timedelta(days=729):cutoff]
                for arm in ARMS:
                    exog = fc[arm]
                    fit = fit_checked(SARIMAX(tr, exog=exog.reindex(tr.index), order=(1, 0, 0), seasonal_order=(1, 0, 0, 7), trend='n',
                        enforce_stationarity=False), 'sarimax', attempts, dict(configuration=arm, state=state, year=2026,
                        refit=str((cutoff+pd.Timedelta(days=1)).date()), training_end=str(cutoff.date())))
                    previous = cutoff+pd.Timedelta(days=1)
                    for origin in sorted(group.origin.unique()):
                        origin = pd.Timestamp(origin); new = y.loc[previous:origin-pd.Timedelta(days=1)]
                        if len(new):
                            fit = fit.extend(new, exog=exog.reindex(new.index))
                        future = pd.date_range(origin, periods=21)
                        pred = np.asarray(fit.forecast(21, exog=exog.reindex(future)))
                        a = group[group.origin.eq(origin)].copy(); a['prediction'] = [pred[int(h)-1] for h in a.horizon]
                        a['actual'] = observed.reindex(pd.DatetimeIndex(a.date)).to_numpy()
                        a['mase_scale'] = engine.scale(data, state, 2026); a['model'] = 'sarimax'; a['arm'] = arm
                        rows.append(a)
                        updates.append(dict(arm=arm, state=state, origin=str(origin.date()), training_end=str(cutoff.date()),
                                            context_end=str((origin-pd.Timedelta(days=1)).date())))
                        previous = origin
                    pd.concat(rows).to_csv(out/'checkpoint.csv', index=False)
                    dump(out/'fit_attempts.json', attempts); dump(out/'deployments.json', updates)
        d = pd.concat(rows)
        assert len(d) == len(cases)*len(ARMS) and np.isfinite(d.prediction).all()
        d.to_csv(out/'predictions.csv', index=False)
        dump(out/'run.json', dict(model='sarimax', completed_utc=datetime.now(timezone.utc).isoformat(), rows=len(d), attempts=len(attempts),
            arms=ARMS, predictions_sha256=sha(out/'predictions.csv'), protocol_sha256=sha(OUT/cohort/'protocol.json')))
    except BaseException:
        (out/'failure.txt').write_text(traceback.format_exc()); dump(out/'fit_attempts.json', attempts); raise


def run(cohort, worker):
    reg = json.loads((OUT/'registration.json').read_text())
    assert sha(OUT/cohort/'protocol.json') == reg['protocols'][cohort]
    protocol = json.loads((OUT/cohort/'protocol.json').read_text())
    for f, h in protocol['input_hashes'].items():
        assert sha(ROOT/f) == h, f
    import mta_model_engine_v1 as engine
    engine.OUT = OUT/cohort
    sarimax(engine, cohort) if worker == 'sarimax' else regression(engine, cohort, worker)


if __name__ == '__main__':
    a = argparse.ArgumentParser()
    a.add_argument('action', choices=['prepare', *MODELS])
    a.add_argument('--cohort', choices=COHORTS, default='event_window')
    args = a.parse_args()
    prepare() if args.action == 'prepare' else run(args.cohort, args.action)
