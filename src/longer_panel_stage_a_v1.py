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
    summary = dict(event_cases=len(ev), ordinary_cases=len(od), event_by_year=ev.groupby('year').size().to_dict(),
                   ordinary_by_year=od.groupby('year').size().to_dict(), family_year_clusters=int(ev[['family', 'year']].drop_duplicates().shape[0]),
                   new_anchor_rows=len(new), placebo_rows_2020_2021=int(len(fake)-len(pd.read_csv(PLACEBO_2225))),
                   unchecked_dry_run=bool(allow_unchecked))
    dump(out/'design_summary.json', summary)
    print(json.dumps(summary, indent=1, default=str))
    return summary


if __name__ == '__main__':
    a = argparse.ArgumentParser()
    a.add_argument('action', choices=['prepare'])
    a.add_argument('--allow-unchecked', action='store_true')
    a.add_argument('--out', default=str(OUT))
    args = a.parse_args()
    if args.allow_unchecked and Path(args.out).resolve() == OUT.resolve():
        raise SystemExit('Unchecked calendars may only be used for a dry run outside the registered folder')
    prepare(args.out, args.allow_unchecked)
