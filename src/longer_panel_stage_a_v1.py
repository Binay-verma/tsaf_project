"""Longer panel, Stage A: event years 2022-2025 for Delhi, Karnataka and Maharashtra (local models).

Extends the document-aligned study (event years 2024-2025) backwards by two event years using
calendar years 2020-2021 from review/longer_panel_v1/calendar_entries_2014_2021.csv, which must be
checked by a person first (`checked_by` and `check_date` filled). Everything else follows the
existing study:

- anchors 2022-2025: results/calendar_semantics_v2/anchors_2022_2025.csv, unchanged;
- placebo anchors 2022-2025: results/calendar_recenter_recovery_v1/placebo_anchors.csv, unchanged;
  2020-2021 placebos by the same seeded rule (shifts +/-28/35/42, same-year window, no overlap);
- conventions: first Diwali anchor = national main date (extended_validation.MAIN), second = the
  state's listed second Diwali holiday; weekend-excluded festivals stay flagged;
- event cases: union of +/-3-day windows around every anchor of a family/state/year, leads 1, 7, 14
  (this rule reproduces the existing 528 cases for 2024-2025 exactly; checked in prepare);
- ordinary cases: the existing rotating-weekday rule (reproduces the existing 216 for 2024-2025); if the
  requested weekday has no eligible date, the next weekday is used (date-only fallback, never needed for 2024-2025);
- local models: rich Ridge, float32 LightGBM, leaf-2 LightGBM, SARIMAX(1,0,0)(1,0,0,7); parameters for
  2022-2023 selected by the unchanged strong_refit / stable_tree procedures on a pre-year block
  (ordinary calendar only, no festival flags), 2024-2025 parameters reused;
- arms: calendar, zero5, day5, pooled_day5, window5, pooled_window5, placebo_day5, placebo_window5.

Actions:
  prepare [--allow-unchecked --out DIR]   build ledgers, cases and protocol (unchecked only for dry runs)
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd
from forecasting import ROOT
from festival_feature_design import sha, dump, FAMILIES

OUT = ROOT/'results/longer_panel_stage_a_v1'
ENTRIES = ROOT/'review/longer_panel_v1/calendar_entries_2014_2021.csv'
ANCHORS_2225 = ROOT/'results/calendar_semantics_v2/anchors_2022_2025.csv'
PLACEBO_2225 = ROOT/'results/calendar_recenter_recovery_v1/placebo_anchors.csv'
ANNUAL = ROOT/'results/extended_validation/regional_calendar_date_audit.csv'
COMPOSED = ROOT/'results/calendar_recenter_recovery_v1/analysis/breadth'
STATES = ['Delhi', 'Karnataka', 'Maharashtra']
NEW_CAL_YEARS = [2020, 2021]
EVENT_YEARS = [2022, 2023, 2024, 2025]
ARMS = ['calendar', 'zero5', 'day5', 'pooled_day5', 'window5', 'pooled_window5', 'placebo_day5', 'placebo_window5']
MODELS = ['ridge', 'lightgbm', 'lightgbm_capacity2', 'sarimax']
SCOPE = {'Delhi': ['Diwali', 'Dussehra', 'Holi'],
         'Karnataka': ['Diwali', 'Dussehra', 'Ganesh_Chaturthi', 'Ugadi_Gudi_Padwa'],
         'Maharashtra': ['Diwali', 'Dussehra', 'Ganesh_Chaturthi', 'Holi', 'Ugadi_Gudi_Padwa']}
KEY = ['family', 'state', 'year', 'date', 'horizon']


def new_anchors(allow_unchecked=False):
    from extended_validation import MAIN
    t = pd.read_csv(ENTRIES, dtype=str).fillna('')
    t = t[t.year.astype(int).isin(NEW_CAL_YEARS) & t.date.ne('')]
    if not allow_unchecked:
        missing = t[t.checked_by.eq('') | t.check_date.eq('')]
        if len(missing):
            raise ValueError(f'{len(missing)} calendar rows for 2020-2021 are not checked by a person yet')
    rows, sens = [], []
    for r in t.itertuples(index=False):
        y = int(r.year)
        if r.family == 'Diwali' and r.role == 'annual_as_issued_anchor':
            main = MAIN[y]
            if r.date != main:
                sens.append(dict(state=r.state, year=y, family='Diwali', national_main=main, state_listed=r.date))
            rows.append(dict(family='Diwali', state=r.state, year=y, date=main, label='Diwali', role='national_main',
                             source=r.document_url, evidence=f'national main (extended_validation.MAIN); state-listed {r.date}; {r.candidate_source}; checked {r.checked_by} {r.check_date}'))
        else:
            role = 'regional_subsidiary' if r.role == 'regional_subsidiary' else 'annual_as_issued_anchor'
            rows.append(dict(family=r.family, state=r.state, year=y, date=r.date, label=r.family, role=role,
                             source=r.document_url, evidence=f'{r.candidate_source}; checked {r.checked_by} {r.check_date}'))
    a = pd.DataFrame(rows)
    for st in STATES:
        for y in NEW_CAL_YEARS:
            have = set(a[(a.state == st) & (a.year == y)].family)
            assert have == set(SCOPE[st]), (st, y, sorted(have))
    return a, pd.DataFrame(sens)


def placebos(anchors, seed=42):
    rng = np.random.default_rng(seed)
    out = []
    for (state, year, family), g in anchors.groupby(['state', 'year', 'family'], sort=True):
        true = anchors[anchors.state.eq(state) & anchors.year.eq(year)]
        prohibited = {d for date in pd.to_datetime(true.date) for d in pd.date_range(date-pd.Timedelta(days=3), date+pd.Timedelta(days=3))}
        valid = []
        for shift in [-42, -35, -28, 28, 35, 42]:
            shifted = pd.to_datetime(g.date)+pd.Timedelta(days=shift)
            window = {d for date in shifted for d in pd.date_range(date-pd.Timedelta(days=3), date+pd.Timedelta(days=3))}
            if all(d.year == year for d in window) and not window.intersection(prohibited):
                valid.append(shift)
        assert valid, (state, year, family)
        shift = int(rng.choice(valid))
        for r in g.itertuples(index=False):
            out.append(dict(state=state, year=int(year), family=family, date=str((pd.Timestamp(r.date)+pd.Timedelta(days=shift)).date()),
                            original_date=r.date, shift_days=shift))
    return pd.DataFrame(out)


def event_cases(anchors, years):
    rows = []
    a = anchors.assign(date=pd.to_datetime(anchors.date))
    for (f, s, y), g in a[a.year.isin(years)].groupby(['family', 'state', 'year']):
        days = sorted({d for x in g.date for d in pd.date_range(x-pd.Timedelta(days=3), x+pd.Timedelta(days=3))})
        for d in days:
            for h in [1, 7, 14]:
                rows.append(dict(family=f, state=s, year=int(y), date=str(d.date()), horizon=h, origin=str((d-pd.Timedelta(days=h-1)).date())))
    return pd.DataFrame(rows).sort_values(['state', 'origin', 'horizon', 'family']).reset_index(drop=True)


def ordinary_cases(anchors, years):
    annual = pd.read_csv(ANNUAL)
    rows = []
    for state in STATES:
        for year in years:
            annual_dates = annual[annual.state.eq(state) & annual.year.eq(year) & annual.in_annual_schedule].date
            named = anchors[anchors.state.eq(state) & anchors.year.eq(year)].date
            blocked = {d for x in pd.to_datetime(list(annual_dates)+list(named)) for d in pd.date_range(x-pd.Timedelta(days=3), x+pd.Timedelta(days=3))}
            for month in range(1, 13):
                requested = (month-1+3*(year-2024)) % 7
                possible, fallback = [], 0
                for fallback in range(7):  # fallback (date-only, fixed): next weekday if the requested one has no candidate
                    weekday = (requested+fallback) % 7
                    possible = [d for d in pd.date_range(f'{year}-{month:02d}-01', periods=31)
                                if d.month == month and d.weekday() == weekday and d not in blocked
                                and pd.Timestamp(f'{year}-01-14') <= d <= pd.Timestamp(f'{year}-12-18')]
                    if possible:
                        break
                if not possible:
                    raise ValueError(('no ordinary candidate', state, year, month))
                d = possible[0]
                for h in [1, 7, 14]:
                    rows.append(dict(family='Ordinary', state=state, year=year, date=str(d.date()), horizon=h,
                                     origin=str((d-pd.Timedelta(days=h-1)).date()), month=month, requested_weekday=requested, weekday_fallback=fallback))
    return pd.DataFrame(rows).sort_values(['state', 'origin', 'horizon']).reset_index(drop=True)


def existing_cases(cohort):
    d = pd.read_csv(COMPOSED/cohort/'predictions_compared.csv')
    d = d[d.version.eq('document_aligned') & d.model.eq('ridge') & d.arm.eq('calendar')]
    return d[['family', 'state', 'year', 'date', 'horizon']].drop_duplicates()


def same(a, b):
    k = ['family', 'state', 'year', 'date', 'horizon']
    a = a[k].astype(str).drop_duplicates(); b = b[k].astype(str).drop_duplicates()
    return len(a) == len(b) and len(a.merge(b, on=k)) == len(a)


def frames(index, state, anchors, fake):
    """Calendar base plus typed/pooled day/window, zero and placebo channels from the given ledgers."""
    from extended_validation import features
    base, cols, _ = features(index, state)
    base = base[cols['B_calendar']].copy()

    def typed(ledger, kind):
        v = {}
        for family in FAMILIES:
            roots = pd.to_datetime(ledger[ledger.state.eq(state) & ledger.family.eq(family)].date)
            dates = roots if kind == 'day' else [d for r in roots for d in pd.date_range(r-pd.Timedelta(days=3), r+pd.Timedelta(days=3))]
            v[f'{family}_{kind}'] = index.isin(dates).astype(float)
        return pd.DataFrame(v, index=index)
    out = {'calendar': base, 'zero5': pd.concat([base, pd.DataFrame(0., index=index, columns=[f'zero_{i}' for i in range(5)])], axis=1)}
    for kind in ['day', 'window']:
        t = typed(anchors, kind)
        pooled = pd.DataFrame({f'event_{kind}': t.any(axis=1).astype(float)}, index=index)
        for j in range(1, 5):
            pooled[f'padding_{j}'] = 0.
        out[f'{kind}5'] = pd.concat([base, t], axis=1)
        out[f'pooled_{kind}5'] = pd.concat([base, pooled], axis=1)
        out[f'placebo_{kind}5'] = pd.concat([base, typed(fake, kind)], axis=1)
    return {arm: out[arm] for arm in ARMS}


INPUTS = ['src/longer_panel_stage_a_v1.py', 'src/longer_panel_analysis_stage_a_v1.py', 'src/test_longer_panel_stage_a_v1.py',
          'src/breadth_model_engine_v1.py', 'src/robust_baselines.py', 'src/stable_tree_refit.py', 'src/extended_validation.py',
          'src/forecasting.py', 'src/multifestival_models.py', 'data/external/latest_state_energy_GWh.csv',
          'review/longer_panel_v1/calendar_entries_2014_2021.csv', 'results/calendar_semantics_v2/anchors_2022_2025.csv',
          'results/calendar_recenter_recovery_v1/placebo_anchors.csv', 'results/extended_validation/regional_calendar_date_audit.csv',
          'results/strong_refit_v1/selected.csv', 'results/stable_tree_refit_v2/selected.csv',
          'results/strong_refit_v1/protocol.json', 'results/stable_tree_refit_v2/protocol.json']


def prepare(out=OUT, allow_unchecked=False):
    out = Path(out)
    if out.exists():
        raise FileExistsError('Preserve the registered protocol; create a new version')
    new, sens = new_anchors(allow_unchecked)
    old = pd.read_csv(ANCHORS_2225)
    anchors = pd.concat([new, old], ignore_index=True).sort_values(['state', 'year', 'family', 'date']).reset_index(drop=True)
    fake = pd.concat([placebos(new), pd.read_csv(PLACEBO_2225)], ignore_index=True)
    ev = event_cases(anchors, EVENT_YEARS); od = ordinary_cases(anchors, EVENT_YEARS)
    assert same(ev[ev.year.isin([2024, 2025])], existing_cases('event_window')), 'event rule does not reproduce the existing 2024-2025 cases'
    assert same(od[od.year.isin([2024, 2025])], existing_cases('ordinary')), 'ordinary rule does not reproduce the existing 2024-2025 cases'
    out.mkdir(parents=True)
    anchors.to_csv(out/'anchors_2020_2025.csv', index=False); fake.to_csv(out/'placebo_anchors_2020_2025.csv', index=False)
    sens.to_csv(out/'sensitivity_state_listed_diwali.csv', index=False)
    for name, c in [('event_window', ev), ('ordinary', od)]:
        (out/name).mkdir()
        c.to_csv(out/name/'window_cases.csv', index=False); c.to_csv(out/name/'primary_cases.csv', index=False)
    sel = {}
    for name, parent in [('ridge', 'strong_refit_v1'), ('tree', 'stable_tree_refit_v2')]:
        d = Path(str(out)+f'_selection_{name}'); d.mkdir()
        q = json.loads((ROOT/f'results/{parent}/protocol.json').read_text())
        q.update(experiment=d.name, created_utc=datetime.now(timezone.utc).isoformat(), years=[2022, 2023], modes=['rich_calendar'],
                 refits=['monthly'], status=('Parameter selection for Stage A event years 2022-2023 by the unchanged procedure of '
                 f'results/{parent}; ordinary calendar only (no festival flags). Its full-year calendar-only predictions are a by-product.'))
        dump(d/'protocol.json', q); sel[name] = str(d.relative_to(ROOT)) if d.is_relative_to(ROOT) else str(d)
    for name in ['event_window', 'ordinary']:
        dump(out/name/'protocol.json', dict(
            experiment=f'{out.name}/{name}', created_utc=datetime.now(timezone.utc).isoformat(), author='Binay Verma',
            status=('Registered before any Stage A forecast for event years 2022-2023 and before parameter selection for those years. '
                    'Event years 2024-2025 and their arms were already inspected; 2022-2023 are new to every model and arm.'),
            question='Is the typed-minus-pooled ordering stable across four event years (2022-2025) and 20 family-year clusters?',
            arms=ARMS, models=MODELS, event_years=EVENT_YEARS, calendar_years='2020-2025', parameter_selection=sel,
            conventions=['first Diwali anchor = national main date; second = state-listed second Diwali holiday',
                         'festivals omitted from a state list only because of a weekend stay flagged',
                         'ordinary weekday fallback: next weekday when the requested weekday has no eligible date'],
            sensitivities=['new years only (2022-2023) versus old years only (2024-2025)'],
            recorded_not_run=('Karnataka 2021 state-listed Diwali 2021-11-03 versus national 2021-11-04 '
                              '(sensitivity_state_listed_diwali.csv); it affects only a training-context year'),
            primary=('typed minus pooled balanced event MASE at lead 1, day and window representations, for the four local '
                     'specifications (8 cells); exact sign-flip over 20 family-year clusters, Holm across the 8 cells, alpha 0.05'),
            secondary=('all 24 local cells (leads 1/7/14); sign by year (4 years) and leave-one-family-out; placebo and zero controls; '
                       'ordinary-day costs; decision rules (follow previous-year winner, equal-weight average) for 2023-2025'),
            interpretation=('An ordering is called supported only if Holm-adjusted p < 0.05 and its sign holds in at least 3 of 4 years; '
                            'otherwise not established. Not detected is not equivalence. Retrospective; calendars checked by a person.'),
            input_hashes={f: sha(ROOT/f) for f in INPUTS},
            design_hashes={'window_cases.csv': sha(out/name/'window_cases.csv'), 'primary_cases.csv': sha(out/name/'primary_cases.csv'),
                           '../anchors_2020_2025.csv': sha(out/'anchors_2020_2025.csv'),
                           '../placebo_anchors_2020_2025.csv': sha(out/'placebo_anchors_2020_2025.csv')}))
    summary = dict(event_cases=len(ev), ordinary_cases=len(od), event_by_year=ev.groupby('year').size().to_dict(),
                   ordinary_by_year=od.groupby('year').size().to_dict(), family_year_clusters=int(ev[['family', 'year']].drop_duplicates().shape[0]),
                   new_anchor_rows=len(new), placebo_rows_2020_2021=int(len(fake)-len(pd.read_csv(PLACEBO_2225))),
                   unchecked_dry_run=bool(allow_unchecked))
    dump(out/'design_summary.json', summary)
    print(json.dumps(summary, indent=1, default=str))
    return summary


def bound(dates):
    assert pd.Timestamp(min(dates)) >= pd.Timestamp('2020-01-01') and pd.Timestamp(max(dates)) <= pd.Timestamp('2025-12-31')


def selected(model_name, year):
    if year in (2024, 2025):
        path = ROOT/('results/strong_refit_v1/selected.csv' if model_name == 'ridge' else 'results/stable_tree_refit_v2/selected.csv')
    else:
        path = Path(str(OUT)+('_selection_ridge' if model_name == 'ridge' else '_selection_tree'))/'selected.csv'
    return pd.read_csv(path)


def regression(engine, worker):
    """Same as the registered Ziel/breadth regression: monthly refits, rich-history design with calendar columns
    replaced in place by the arm frame at the target date, extra channels appended; parameters fixed per year."""
    import hashlib, time, traceback
    from robust_baselines import design_frame, fitting_cases, make_model
    p, out, cases, data = engine.setup(worker)
    anchors = pd.read_csv(engine.OUT.parent/'anchors_2020_2025.csv'); fake = pd.read_csv(engine.OUT.parent/'placebo_anchors_2020_2025.csv')
    model_name = 'ridge' if worker == 'ridge' else 'lightgbm'
    fixed = json.loads((ROOT/('results/strong_refit_v1/protocol.json' if model_name == 'ridge' else 'results/stable_tree_refit_v2/protocol.json')).read_text())
    rows, fits = [], []
    try:
        for (state, year, horizon), group in cases.groupby(['state', 'year', 'horizon']):
            observed = data[state]; fc = frames(data.index, state, anchors, fake)
            base, _ = design_frame(observed, state, int(horizon), 'rich_calendar')
            cal = list(fc['calendar'].columns)
            sel = selected(model_name, int(year))
            chosen = sel[sel.state.eq(state) & sel.year.eq(year) & sel.horizon.eq(horizon) & sel['mode'].eq('rich_calendar') & sel.model.eq(model_name)]
            assert len(chosen) == 1, (state, year, horizon)
            params = json.loads(chosen.parameters.iloc[0])
            if worker == 'lightgbm_capacity2':
                params['min_child_samples'] = 2
            for arm in ARMS:
                sh = fc[arm].reindex(data.index+pd.Timedelta(days=int(horizon)-1)).copy(); sh.index = data.index
                x = base.copy(); x[cal] = sh.iloc[:, :13].to_numpy(); x = pd.concat([x, sh.iloc[:, 13:]], axis=1)
                if model_name == 'lightgbm':
                    x = x.astype(np.float32)
                for month, seg in group.groupby(group.origin.dt.to_period('M')):
                    refit = pd.Timestamp(month.start_time); cutoff = refit-pd.Timedelta(days=1)
                    bound([cutoff-pd.Timedelta(days=729)+pd.Timedelta(days=int(horizon)-1), cutoff, seg.date.min(), seg.date.max()])
                    xx, yy, log = fitting_cases(x, observed, int(horizon), cutoff)
                    assert pd.Timestamp(log['training_target_max']) < refit <= seg.origin.min()
                    q = x.reindex(pd.DatetimeIndex(seg.origin)).to_numpy()
                    m = make_model(model_name, params, fixed).fit(xx, yy)
                    a = seg.copy(); a['prediction'] = m.predict(q); a['mase_scale'] = engine.scale(data, state, int(year))
                    a['model'] = worker; a['arm'] = arm; rows.append(a)
                    fits.append(dict(model=worker, arm=arm, state=state, year=int(year), horizon=int(horizon), refit=str(refit.date()),
                                     parameters=params, training_X_sha256=hashlib.sha256(xx.tobytes()).hexdigest(),
                                     query_X_sha256=hashlib.sha256(q.tobytes()).hexdigest(), **log))
            pd.concat(rows).to_csv(out/'checkpoint.csv', index=False); dump(out/'fit_log.json', fits)
            print(worker, state, year, horizon, flush=True)
        d = pd.concat(rows, ignore_index=True)
        assert len(d) == len(cases)*len(ARMS) and np.isfinite(d.prediction).all()
        d.to_csv(out/'predictions.csv', index=False)
        dump(out/'run.json', dict(model=worker, completed_utc=datetime.now(timezone.utc).isoformat(), rows=len(d),
                                  predictions_sha256=sha(out/'predictions.csv'), protocol_sha256=sha(engine.OUT/'protocol.json')))
    except BaseException:
        (out/'failure.txt').write_text(traceback.format_exc()); dump(out/'fit_log.json', fits); raise


def run(cohort, worker):
    import breadth_model_engine_v1 as engine
    engine.OUT = OUT/cohort; engine.ARMS = ARMS; engine.EXTRA = []; engine.ledger_bound = bound
    anchors = pd.read_csv(OUT/'anchors_2020_2025.csv'); fake = pd.read_csv(OUT/'placebo_anchors_2020_2025.csv')
    engine.frames = lambda index, state: frames(index, state, anchors, fake)
    for name in ['ridge', 'tree']:
        assert (Path(str(OUT)+f'_selection_{name}')/'selected.csv').exists(), 'run the 2022-2023 parameter selection first'
    engine.sarimax() if worker == 'sarimax' else regression(engine, worker)


if __name__ == '__main__':
    a = argparse.ArgumentParser()
    a.add_argument('action', choices=['prepare', *MODELS])
    a.add_argument('--cohort', choices=['event_window', 'ordinary'], default='event_window')
    a.add_argument('--allow-unchecked', action='store_true')
    a.add_argument('--out', default=str(OUT))
    args = a.parse_args()
    if args.allow_unchecked and Path(args.out).resolve() == OUT.resolve():
        raise SystemExit('Unchecked calendars may only be used for a dry run outside the registered folder')
    prepare(args.out, args.allow_unchecked) if args.action == 'prepare' else run(args.cohort, args.action)
