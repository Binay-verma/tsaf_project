"""Prespecified matched non-event secondary cohort; same frozen model rules."""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import json
import time
import traceback
import numpy as np
import pandas as pd
import festival_feature_experiment as experiment
from festival_feature_design import ROOT, OUT as PARENT, KEY, sha, dump

OUT = ROOT/'results/festival_feature_spillover_v2'
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
    for f in ['results/strong_refit_v1/predictions.csv', 'results/stable_tree_refit_v2/predictions.csv']:
        p['input_hashes'][f] = sha(ROOT/f)
    p['regression_baseline_reference'] = 'This wrapper implements the same fixed fitting specification and compares ordinary-calendar outputs against original full-daily saved forecasts, since parent event-window-only predictions do not cover non-event controls.'
    p['design_hashes'] = {f: sha(OUT/f) for f in ['primary_cases.csv', 'window_cases.csv', 'anchors_2022_2025.csv', 'placebo_anchors.csv', 'date_only_matching.csv']}
    dump(OUT/'protocol.json', p)
    print('FROZEN72matched non-event cases;3arms;6model variants; date-only matching')


def regression(worker):
    from robust_baselines import design_frame, fitting_cases, make_model
    from festival_feature_design import frames
    from forecasting import ROOT, load_data
    p, out, cases, data = experiment.setup(worker)
    model_name = 'ridge' if worker == 'ridge' else 'lightgbm'
    old = 'strong_refit_v1' if model_name == 'ridge' else 'stable_tree_refit_v2'
    selected = pd.read_csv(ROOT/f'results/{old}/selected.csv')
    fixed = json.loads((ROOT/f'results/{old}/protocol.json').read_text())
    old_predictions = pd.read_csv(ROOT/f'results/{old}/predictions.csv', parse_dates=['origin', 'date'])
    old_predictions = old_predictions[old_predictions.model.eq(model_name) & old_predictions['mode'].eq('rich_calendar') & old_predictions.schedule.eq('monthly')]
    rows, fits, reproduction = [], [], []
    started = time.perf_counter()
    try:
        for (state, year, h), group in cases.groupby(['state', 'year', 'horizon']):
            base, _ = design_frame(data[state], state, int(h), 'rich_calendar')
            chosen = selected[selected.state.eq(state) & selected.year.eq(year) & selected.horizon.eq(h) & selected.model.eq(model_name) & selected['mode'].eq('rich_calendar')]
            assert len(chosen) == 1
            params = json.loads(chosen.parameters.iloc[0])
            if worker == 'lightgbm_capacity2':
                params['min_child_samples'] = 2
            fc = frames(data.index, state)
            for arm in ARMS:
                extra = fc[arm].iloc[:, 13:].reindex(data.index+pd.Timedelta(days=int(h)-1)).copy()
                extra.index = data.index
                x = pd.concat([base, extra], axis=1)
                if model_name == 'lightgbm':
                    x = x.astype(np.float32)
                chunks = []
                for month, segment in group.groupby(group.origin.dt.to_period('M')):
                    refit = pd.Timestamp(month.start_time)
                    cutoff = refit-pd.Timedelta(days=1)
                    experiment.ledger_bound([cutoff-pd.Timedelta(days=729)+pd.Timedelta(days=int(h)-1), cutoff, segment.date.min(), segment.date.max()])
                    xx, yy, log = fitting_cases(x, data[state], int(h), cutoff)
                    assert pd.Timestamp(log['training_target_max']) < refit <= segment.origin.min()
                    model = make_model(model_name, params, fixed).fit(xx, yy)
                    query = x.reindex(pd.DatetimeIndex(segment.origin)).to_numpy()
                    a = segment.copy(); a['prediction'] = model.predict(query)
                    a['mase_scale'] = experiment.scale(data, state, int(year)); a['model'] = worker; a['arm'] = arm
                    chunks.append(a)
                    fits.append(dict(model=worker, arm=arm, state=state, year=int(year), horizon=int(h), refit=str(refit.date()), parameters=params,
                        feature_count=xx.shape[1], training_X_sha256=__import__('hashlib').sha256(xx.tobytes()).hexdigest(),
                        training_y_sha256=__import__('hashlib').sha256(yy.tobytes()).hexdigest(),
                        query_X_sha256=__import__('hashlib').sha256(query.tobytes()).hexdigest(), **log))
                a = pd.concat(chunks, ignore_index=True)
                if arm == 'calendar' and worker != 'lightgbm_capacity2':
                    cols = ['state', 'year', 'origin', 'date', 'horizon']
                    c = a.merge(old_predictions[cols+['prediction']], on=cols, suffixes=('_new', '_old'), validate='one_to_one')
                    assert len(c) == len(group)
                    np.testing.assert_allclose(c.prediction_new, c.prediction_old, rtol=1e-9, atol=1e-7)
                    reproduction.append(dict(state=state, year=int(year), horizon=int(h), maxdiff=float(abs(c.prediction_new-c.prediction_old).max())))
                rows.append(a)
                pd.concat(rows, ignore_index=True).to_csv(out/'checkpoint.csv', index=False)
                dump(out/'fit_log.json', fits)
            print(worker, state, year, h, 'non-event complete', flush=True)
        d = pd.concat(rows, ignore_index=True)
        assert len(d) == len(cases)*len(ARMS) and np.isfinite(d.prediction).all()
        d.to_csv(out/'predictions.csv', index=False)
        dump(out/'baseline_reproduction.json', reproduction)
        dump(out/'run.json', dict(model=worker, completed_utc=datetime.now(timezone.utc).isoformat(), rows=len(d), fits=len(fits), arms=ARMS,
            cases_per_arm=len(cases), seconds=time.perf_counter()-started, predictions_sha256=sha(out/'predictions.csv'), protocol_sha256=sha(OUT/'protocol.json')))
    except Exception:
        (out/'failure.txt').write_text(traceback.format_exc())
        dump(out/'fit_log.json', fits)
        raise


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
            regression(action)
