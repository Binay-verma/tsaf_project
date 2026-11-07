"""Step 1 of the longer-panel study: data check and calendar entry template (no forecasting, no outcomes).

Reads only the source file and the existing anchor ledger. Writes review/longer_panel_v1/.
Run from the repository root: python src/longer_panel_scan_v1.py
"""
import json
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'review/longer_panel_v1'
STATES = ['Delhi', 'Karnataka', 'Maharashtra']
NEW_CALENDAR_YEARS = list(range(2014, 2022))   # 2022-2025 already in results/calendar_semantics_v2/anchors_2022_2025.csv
EVENT_YEARS = list(range(2016, 2026))          # each needs the two previous years as context


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    d = pd.read_csv(ROOT/'data/external/POSOCO_data.csv')
    d.index = pd.to_datetime(d.yyyymmdd.astype(str))
    rows = []
    for st in STATES:
        s = d[f'{st}: EnergyMet']
        for y in range(2013, 2026):
            x = s.reindex(pd.date_range(f'{y}-01-01', f'{y}-12-31'))
            rows.append(dict(state=st, year=y, missing_or_nonpositive_days=int((x.isna() | (x <= 0)).sum())))
    q = pd.DataFrame(rows)
    q.to_csv(OUT/'data_quality_by_year.csv', index=False)
    a = pd.read_csv(ROOT/'results/calendar_semantics_v2/anchors_2022_2025.csv')
    scope = {st: sorted(a[a.state.eq(st)].family.unique()) for st in STATES}
    t = []
    for st in STATES:
        for y in NEW_CALENDAR_YEARS:
            for fam in scope[st]:
                t.append(dict(state=st, year=y, family=fam, role='annual_as_issued_anchor', date='', label_in_document='',
                              not_listed_this_year='', document_title='', issuing_authority='', document_url='', page='',
                              quoted_line='', candidate_source='', entered_by='', checked_by='', check_date='', notes=''))
            if 'Diwali' in scope[st]:
                t.append(dict(state=st, year=y, family='Diwali', role='regional_subsidiary', date='', label_in_document='',
                              not_listed_this_year='', document_title='', issuing_authority='', document_url='', page='',
                              quoted_line='', candidate_source='', entered_by='', checked_by='', check_date='',
                              notes='Only if the state notice lists a second Diwali-related holiday (e.g. Balipratipada / Diwali Padwa)'))
    pd.DataFrame(t).to_csv(OUT/'calendar_entries_2014_2021.csv', index=False)
    bad = q[q.year.isin(range(2014, 2026))].missing_or_nonpositive_days.max()
    json.dump(dict(created_utc=datetime.now(timezone.utc).isoformat(), states=STATES, event_years=EVENT_YEARS,
                   new_calendar_years=NEW_CALENDAR_YEARS, family_scope=scope, template_rows=len(t),
                   worst_year_2014_2025_bad_days=int(bad), year_2013_bad_days={st: int(q[(q.state == st) & (q.year == 2013)].missing_or_nonpositive_days.iloc[0]) for st in STATES},
                   note=('Event years 2016-2025 (10 years). 2013 is incomplete and is used only as context before 2015, so 2015 is not an event year. '
                         'COVID years 2020-2021 are to be pre-declared as a sensitivity. Calendar rows must be filled from official state '
                         'notifications and checked by a person; machine-found candidates are marked in candidate_source and never used unchecked.')),
              open(OUT/'scan.json', 'w'), indent=1)
    print(q.pivot(index='year', columns='state', values='missing_or_nonpositive_days').to_string()); print(len(t), 'template rows', scope)


if __name__ == '__main__':
    main()
