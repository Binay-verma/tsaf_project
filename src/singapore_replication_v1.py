"""Singapore festival replication: data, calendar, case and feature layer (no data acquired here).

Implements results/singapore_festival_replication_v1/DRAFT_PROTOCOL.json, mirroring
mta_holiday_study.py rules: +/-3-day windows, decision leads 1/7/14 -> model steps 8/14/21
(fixed 7-day observation buffer), 13 ordinary calendar channels, typed/pooled/zero/placebo arms.
Source adapters accept already-loaded tables; the exact EMA/MOM file formats are NOT yet
confirmed, so column handling is explicit and fails loudly. Model runners are not included yet.
"""
import re
import numpy as np
import pandas as pd

FAMILIES = ['Chinese_New_Year', 'Hari_Raya_Puasa', 'Vesak_Day', 'Hari_Raya_Haji', 'Deepavali']
PATTERNS = {'Chinese_New_Year': r'chinese new year', 'Hari_Raya_Puasa': r'hari raya puasa',
            'Vesak_Day': r'vesak', 'Hari_Raya_Haji': r'hari raya haji', 'Deepavali': r'deepavali'}
ARMS = ['calendar', 'zero5', 'day5', 'pooled_day5', 'window5', 'pooled_window5', 'placebo_day5', 'placebo_window5']
FOUNDATION_ARMS = ['history', *ARMS]
SERIES = 'Singapore'
SHIFT_ORDER = [35, -35, 28, -28, 42, -42]
BUFFER = 7
LEADS = (1, 7, 14)
PERIODS = 48


def _cols(frame, required):
    lower = {c.strip().lower(): c for c in frame.columns}
    missing = [r for r in required if r not in lower]
    if missing:
        raise ValueError(f'Missing columns {missing}; confirm the source format before adapting')
    return {r: lower[r] for r in required}


def parse_mom_holidays(frame):
    """MOM public-holiday table with columns date, holiday (case-insensitive) -> date/name rows."""
    c = _cols(frame, ['date', 'holiday'])
    d = pd.DataFrame({'date': pd.to_datetime(frame[c['date']], errors='raise').dt.normalize(),
                      'name': frame[c['holiday']].astype(str).str.strip()})
    if d.duplicated().any():
        raise ValueError('Duplicate holiday rows need review')
    return d.sort_values('date').reset_index(drop=True)


def family_anchors(holidays):
    """Named family anchors from MOM rows; Sunday holidays add the following Monday as a subsidiary
    (Singapore in-lieu rule), unless that Monday is already listed. No dates are invented beyond that rule."""
    rows, used = [], set()
    listed = set(holidays.date)
    for fam, pat in PATTERNS.items():
        m = holidays[holidays.name.str.lower().str.contains(pat, regex=True)]
        for year, g in m.groupby(m.date.dt.year):
            g = g.sort_values('date')
            for i, r in enumerate(g.itertuples()):
                role = 'annual_as_issued_anchor' if i == 0 else 'regional_subsidiary'
                rows.append(dict(state=SERIES, year=int(year), family=fam, date=r.date, role=role, name_as_printed=r.name))
                used.add(r.Index)
                if r.date.weekday() == 6:
                    monday = r.date+pd.Timedelta(days=1)
                    if monday not in listed:
                        rows.append(dict(state=SERIES, year=int(year), family=fam, date=monday, role='regional_subsidiary',
                                         name_as_printed=f'{r.name} (in-lieu Monday by rule)'))
    a = pd.DataFrame(rows)
    if a.empty:
        raise ValueError('No family holidays matched')
    if a.duplicated(['family', 'date']).any():
        raise ValueError('Duplicate family anchors')
    others = holidays.drop(index=list(used))
    return a.sort_values(['date', 'family']).reset_index(drop=True), others.reset_index(drop=True)


def placebos(anchors, all_holiday_dates):
    """Fixed-rule weekday placebos: first shift in SHIFT_ORDER that stays in the year and is >6 days
    from every public holiday (family or not)."""
    blocked = pd.DatetimeIndex(sorted(set(all_holiday_dates) | set(anchors.date)))
    out = []
    for r in anchors.itertuples():
        for s in SHIFT_ORDER:
            p = r.date+pd.Timedelta(days=s)
            if p.year == r.year and (abs((blocked-p).days) > 6).all():
                out.append(dict(state=r.state, year=r.year, family=r.family, date=p, original_date=r.date, shift_days=s))
                break
        else:
            raise ValueError(f'No valid placebo for {r.family} {r.date.date()}')
    return pd.DataFrame(out)


def daily_energy(halfhourly):
    """Half-hourly system demand (date, period, mw) -> daily GWh; only days with all 48 positive periods."""
    c = _cols(halfhourly, ['date', 'period', 'mw'])
    d = pd.DataFrame({'date': pd.to_datetime(halfhourly[c['date']]).dt.normalize(),
                      'period': pd.to_numeric(halfhourly[c['period']], errors='raise').astype(int),
                      'mw': pd.to_numeric(halfhourly[c['mw']], errors='coerce')})
    if d.duplicated(['date', 'period']).any():
        raise ValueError('Duplicate date/period rows must not be summed')
    if not d.period.between(1, PERIODS).all():
        raise ValueError('Unexpected period index')
    wide = d.pivot(index='date', columns='period', values='mw').reindex(columns=range(1, PERIODS+1))
    complete = wide.notna().all(axis=1) & (wide > 0).all(axis=1)
    gwh = (wide.sum(axis=1)*0.5/1000).where(complete)
    gwh = gwh.asfreq('D')
    return gwh.rename(SERIES).to_frame()


def cases_for(cohort, anchors, other_holidays, years=(2024, 2025)):
    rows = []
    if cohort == 'event_window':
        mains = anchors[anchors.role.ne('regional_subsidiary') & anchors.year.isin(years)]
        targets = [(r.family, d) for r in mains.itertuples() for d in pd.date_range(r.date-pd.Timedelta(days=3), periods=7)]
    elif cohort == 'ordinary':
        roots = pd.DatetimeIndex(list(anchors.date)+list(other_holidays.date))
        blocked = {d for r in roots for d in pd.date_range(r-pd.Timedelta(days=3), r+pd.Timedelta(days=3))}
        targets = []
        for y in years:
            for m in range(1, 13):
                weekday = (m-1+(y-years[0])*12) % 7  # rotating weekday, fixed before data
                cands = [d for d in pd.date_range(f'{y}-{m:02d}-01', periods=pd.Timestamp(y, m, 1).days_in_month)
                         if d.weekday() == weekday and d not in blocked]
                if cands:
                    targets.append(('Ordinary', cands[0]))
    else:
        raise ValueError(cohort)
    for fam, target in targets:
        for lead in LEADS:
            decision = target-pd.Timedelta(days=lead-1)
            origin = decision-pd.Timedelta(days=BUFFER)
            rows.append(dict(family=fam, state=SERIES, year=int(target.year), date=str(target.date()), origin=str(origin.date()),
                             horizon=lead+BUFFER, decision_lead=lead, decision_origin=str(decision.date())))
    d = pd.DataFrame(rows)
    if d.duplicated(['family', 'date', 'decision_lead']).any():
        raise ValueError('Duplicate cases')
    return d.sort_values(['family', 'date', 'decision_lead']).reset_index(drop=True)


def frames(index, anchors, fake):
    cols = {f'dow_{j}': (index.dayofweek == j).astype(float) for j in range(7)}
    for j in [1, 2, 3]:
        cols.update({f'sin_{j}': np.sin(2*np.pi*j*index.dayofyear/365.2425), f'cos_{j}': np.cos(2*np.pi*j*index.dayofyear/365.2425)})
    base = pd.DataFrame(cols, index=index)
    result = {'history': pd.DataFrame(index=index), 'calendar': base,
              'zero5': pd.concat([base, pd.DataFrame(0., index=index, columns=[f'zero_{j}' for j in range(5)])], axis=1)}
    for prefix, ledger in [('', anchors), ('placebo_', fake)]:
        for kind in ['day', 'window']:
            event = {}
            for fam in FAMILIES:
                roots = ledger[ledger.family.eq(fam)].date
                dates = roots if kind == 'day' else [d for r in roots for d in pd.date_range(r-pd.Timedelta(days=3), r+pd.Timedelta(days=3))]
                event[fam+'_'+kind] = index.isin(pd.DatetimeIndex(dates)).astype(float)
            typed = pd.DataFrame(event, index=index)
            result[prefix+kind+'5'] = pd.concat([base, typed], axis=1)
            if not prefix:
                pooled = pd.DataFrame({'event_'+kind: typed.any(axis=1).astype(float)}, index=index)
                for j in range(1, 5):
                    pooled['padding_'+str(j)] = 0.
                result['pooled_'+kind+'5'] = pd.concat([base, pooled], axis=1)
    return result


def context_ok(observed, origin, context=730):
    """True if all context days before origin are recorded (scored labels are never imputed; contexts
    with gaps are reported, not silently filled)."""
    dates = pd.date_range(pd.Timestamp(origin)-pd.Timedelta(days=context), periods=context)
    v = observed.reindex(dates).to_numpy(dtype=float).ravel()
    return bool(np.isfinite(v).all() and (v > 0).all())
