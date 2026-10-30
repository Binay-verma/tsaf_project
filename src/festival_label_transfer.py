"""Fixed-budget supervised-family-label exclusion with matched row controls.

Past target history remains allowed. This is not wholly unseen event exposure.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import time
import traceback
import numpy as np
import pandas as pd
from forecasting import ROOT, load_data
from robust_baselines import design_frame, fitting_cases, make_model
from festival_feature_design import OUT as LEDGER, FAMILIES, frames as typed_frames, sha, dump
from pooled_festival_experiment import frames as pooled_frames
from festival_feature_experiment import scale, ledger_bound

OUT = ROOT/'results/festival_label_transfer_v1'
FEATURES = ['calendar', 'typed_day5', 'pooled_day5']
POLICIES = ['all_rows', 'exclude_family', 'exclude_control']
WORKERS = ['ridge_fixed10', 'tree_fixed20', 'tree_fixed2']


def removed_dates(train_dates, family_dates, prohibited):
    """Deterministic dates only; no response magnitudes used for matching."""
    available = set(pd.DatetimeIndex(train_dates))
    held = sorted(available.intersection({d for a in family_dates for d in pd.date_range(a-pd.Timedelta(days=3), a+pd.Timedelta(days=3))}))
    controls, pairs = set(), []
    for target in held:
        candidates = [target+pd.Timedelta(days=k) for k in [28, -28, 35, -35, 42, -42]]
        eligible = [d for d in candidates if d in available and d.year == target.year and d not in prohibited and d not in controls]
        if not eligible:
            raise ValueError('No date-only matched training-row control for '+str(target.date()))
        selected = eligible[0]
        assert selected.weekday() == target.weekday()
        controls.add(selected)
        pairs.append(dict(family_label_date=str(target.date()), matched_control_date=str(selected.date()), shift_days=int((selected-target).days)))
    assert len(held) == len(controls) and not set(held).intersection(controls)
    return set(held), controls, pairs


def prepare():
    if OUT.exists():
        raise FileExistsError('Version new results; never overwrite a protocol')
    rows = []
    parents = {'event': LEDGER, 'non_event': ROOT/'results/festival_feature_spillover_v2'}
    for cohort, parent in parents.items():
        d = pd.read_csv(parent/'primary_cases.csv')
        d['cohort'] = cohort; rows.append(d)
    cases = pd.concat(rows, ignore_index=True)
    assert len(cases) == 144 and not cases.duplicated(['cohort', 'family', 'state', 'origin', 'horizon']).any()
    OUT.mkdir(parents=True)
    cases.to_csv(OUT/'cases.csv', index=False)
    tree = json.loads((ROOT/'results/stable_tree_refit_v2/protocol.json').read_text())
    paths = ['src/festival_label_transfer.py', 'src/test_festival_label_transfer.py',
        'src/robust_baselines.py', 'src/forecasting.py', 'src/extended_validation.py',
        'src/festival_feature_design.py', 'src/festival_feature_experiment.py', 'src/pooled_festival_experiment.py',
        'data/external/latest_state_energy_GWh.csv',
        'results/festival_features_v1/anchors_2022_2025.csv', 'results/festival_features_v1/placebo_anchors.csv',
        'results/extended_validation/regional_calendar_date_audit.csv',
        'results/stable_tree_refit_v2/protocol.json', 'results/pooled_festival_v1/registration.json',
        'results/pooled_festival_v1/protected_prior_files.json']
    paths += [str((parent/'primary_cases.csv').relative_to(ROOT)) for parent in parents.values()]
    dump(OUT/'protocol.json', dict(created_utc=datetime.now(timezone.utc).isoformat(),
        experiment=OUT.name, status='Exploratory after historical benchmarks; fixed before these exclusion outcomes. No untouched test or external preregistration.',
        question='Can a fixed pooled holiday model transfer predictive information from other family labels when direct fitting labels within+/-3days of one family are excluded?',
        cases='The same72event and72matched non-event cases, all leads1/7/14, separately reported cohorts. No new dates or missing-case intersection.',
        training='Monthly730calendar-day candidate origin window, horizon-purged target labels strictly before refit. Same original27history+13calendar features; all used event-feature dates within2022–2025. Scaler fits only retained rows. No parameter validation/search or reuse of event-exposed selected parameters.',
        workers=WORKERS, feature_arms=FEATURES, row_policies=POLICIES,
        ridge_parameters={'alpha': 10.},
        tree_parameters={'num_leaves': 7, 'n_estimators': 200, 'reg_lambda': 10.},
        leaf_minimum={'tree_fixed20': 20, 'tree_fixed2': 2}, lightgbm_fixed=tree['lightgbm_fixed'],
        features='calendar; named five-family day flags; logical pooled union plus fourzeros. Same true parent ledger. Fixedparameters across all features/row policies.',
        exclusion='For the evaluated family/state, remove all candidate fitting-label dates within+/-3of every named2022–2025anchor of that family, including Diwali subsidiaries. Other families remain. This guarantees zero own-family day-flag support in excluded fitting rows.',
        control='For every available excluded label date in chronological order, remove one distinct same-weekday candidate at first eligible+28,-28,+35,-35,+42,-42days, sameyear/context, excluding+/-3of all annual schedule and registered family anchors. Date/recorded-label availability only, never response magnitudes. Abort if no exact match; do not silently change cohort or budget.',
        exposure='Target-state past electricity observations, annual lags, rolling features and other training rows containing earlier family responses remain allowed. Excluded direct labels are not erased from history. This is supervised family-label exclusion with available target history, not history-free zero-shot, fully unseen-event exposure, causal identification or independent data.',
        metrics='Original positive source labels/pre-year weekly MASE denominator, fixed across training policies; scale can contain past family observations, serving only as evaluation reference. Equal states within year, years within family, families overall; report all families/years/leads/models/policies and paired deltas. No outcome-selected features/budgets.',
        integrity='Preserve all earlier686scientific files via pooled protection manifest. Active pooled inference continues separately and its outputs are not read or used to select settings here. No source/future retrieval or automation changes.',
        input_hashes={f: sha(ROOT/f) for f in paths}, cases_sha256=sha(OUT/'cases.csv'),
        exclusions='No fresh foundation-model weights or inference. No claim that classical label exclusion resolves foundation pretraining exposure or source/calendar review.'))
    print('FROZEN144cases x3workers x3featurearms x3rowpolicies =3888predictions')


def run(worker):
    p = json.loads((OUT/'protocol.json').read_text())
    for name, expected in p['input_hashes'].items():
        assert sha(ROOT/name) == expected, name
    assert sha(OUT/'cases.csv') == p['cases_sha256']
    out = OUT/worker; out.mkdir(exist_ok=True)
    if (out/'started.json').exists():
        raise FileExistsError('Preserve completed/interrupted worker')
    dump(out/'started.json', dict(started_utc=datetime.now(timezone.utc).isoformat(), worker=worker))
    cases = pd.read_csv(OUT/'cases.csv', parse_dates=['date', 'origin'])
    data = load_data('latest')
    ledger = pd.read_csv(LEDGER/'anchors_2022_2025.csv', parse_dates=['date'])
    annual = pd.read_csv(ROOT/'results/extended_validation/regional_calendar_date_audit.csv', parse_dates=['date'])
    model_name = 'ridge' if worker.startswith('ridge') else 'lightgbm'
    params = p['ridge_parameters'] if model_name == 'ridge' else {**p['tree_parameters'], 'min_child_samples': p['leaf_minimum'][worker]}
    fits, rows, pairs_log = [], [], []
    start = time.perf_counter()
    try:
        for (state, year, h), state_cases in cases.groupby(['state', 'year', 'horizon']):
            base, _ = design_frame(data[state], state, int(h), 'rich_calendar')
            typed, pooled = typed_frames(data.index, state), pooled_frames(data.index, state)
            xs = {'calendar': base}
            for name, extra in [('typed_day5', typed['day5'].iloc[:, 13:]), ('pooled_day5', pooled['pooled_day5'].iloc[:, 13:])]:
                aligned = extra.reindex(data.index+pd.Timedelta(days=int(h)-1)).copy(); aligned.index = data.index
                xs[name] = pd.concat([base, aligned], axis=1)
            if model_name == 'lightgbm':
                xs = {name: x.astype(np.float32) for name, x in xs.items()}
            all_dates = list(annual[annual.state.eq(state) & annual.in_annual_schedule].date)+list(ledger[ledger.state.eq(state)].date)
            prohibited = {d for a in all_dates for d in pd.date_range(a-pd.Timedelta(days=3), a+pd.Timedelta(days=3))}
            for (family, month), segment in state_cases.groupby(['family', state_cases.origin.dt.to_period('M')]):
                refit = month.start_time; cutoff = refit-pd.Timedelta(days=1)
                oo = pd.date_range(cutoff-pd.Timedelta(days=729), cutoff-pd.Timedelta(days=int(h)-1))
                dates = oo+pd.Timedelta(days=int(h)-1)
                yy = data[state].reindex(dates).to_numpy()
                raw_x = xs['calendar'].reindex(oo).to_numpy()
                valid = np.isfinite(yy) & np.isfinite(raw_x).all(axis=1)
                training_dates = dates[valid]
                ledger_bound([training_dates.min(), training_dates.max(), segment.date.min(), segment.date.max()])
                family_dates = ledger[ledger.state.eq(state) & ledger.family.eq(family)].date
                excluded, control, matches = removed_dates(training_dates, family_dates, prohibited)
                assert excluded and len(excluded) == len(control)
                ident = dict(state=state, year=int(year), horizon=int(h), family=family, refit=str(refit.date()))
                pairs_log.append(dict(**ident, pairs=matches))
                for feature, x in xs.items():
                    xx, y, log = fitting_cases(x, data[state], int(h), cutoff)
                    np.testing.assert_array_equal(y, yy[valid])
                    assert pd.Timestamp(log['training_target_max']) < refit <= segment.origin.min()
                    query = x.reindex(pd.DatetimeIndex(segment.origin)).to_numpy()
                    for policy in POLICIES:
                        dropped = excluded if policy == 'exclude_family' else control if policy == 'exclude_control' else set()
                        keep = ~training_dates.isin(dropped)
                        assert keep.sum() >= 365
                        if feature == 'typed_day5' and policy == 'exclude_family':
                            assert np.count_nonzero(xx[keep, 40+FAMILIES.index(family)]) == 0
                        model = make_model(model_name, params, p).fit(xx[keep], y[keep])
                        predicted = model.predict(query)
                        a = segment.copy(); a['actual'] = [data.loc[d, state] for d in a.date]
                        a['prediction'] = predicted; a['mase_scale'] = scale(data, state, int(year))
                        a['model'] = worker; a['feature'] = feature; a['policy'] = policy
                        a['arm'] = feature+'__'+policy
                        rows.append(a)
                        fits.append(dict(**ident, feature=feature, policy=policy, parameters=params,
                            candidate_training_n=len(y), retained_training_n=int(keep.sum()), dropped_n=len(dropped),
                            dropped_label_dates=[str(d.date()) for d in sorted(dropped)],
                            fitting_label_dates_sha256=hashlib.sha256('|'.join(str(d.date()) for d in training_dates[keep]).encode()).hexdigest(),
                            retained_label_min=str(training_dates[keep].min().date()),
                            retained_label_max=str(training_dates[keep].max().date()),
                            fitting_y_sha256=hashlib.sha256(y[keep].tobytes()).hexdigest(),
                            fitting_X_sha256=hashlib.sha256(xx[keep].tobytes()).hexdigest(), feature_count=xx.shape[1],
                            nonzero_added_features=np.count_nonzero(xx[keep, 40:], axis=0).astype(int).tolist(), **log))
                pd.concat(rows, ignore_index=True).to_csv(out/'checkpoint.csv', index=False)
                dump(out/'fit_log.json', fits); dump(out/'matched_removal_dates.json', pairs_log)
            print(worker, state, year, h, 'complete', flush=True)
        d = pd.concat(rows, ignore_index=True)
        assert len(d) == 144*9 and d.actual.notna().all() and np.isfinite(d.prediction).all()
        d.to_csv(out/'predictions.csv', index=False)
        dump(out/'run.json', dict(status='completed', worker=worker, rows=len(d), fits=len(fits),
            seconds=time.perf_counter()-start, completed_utc=datetime.now(timezone.utc).isoformat(),
            protocol_sha256=sha(OUT/'protocol.json'), predictions_sha256=sha(out/'predictions.csv')))
    except Exception:
        (out/'failure.txt').write_text(traceback.format_exc()); dump(out/'fit_log.json', fits)
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('action', choices=['prepare']+WORKERS)
    action = parser.parse_args().action
    prepare() if action == 'prepare' else run(action)
