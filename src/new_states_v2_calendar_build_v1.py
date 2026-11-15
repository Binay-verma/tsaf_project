"""Build the second-test calendar (seven states, anchors 2015-2025) from the triage and the author's decisions.

No forecasting, no outcomes. Inputs:
  review/new_states_v2/triage/matched_all.csv     209 rows whose date agrees with an author-verified first-study date
  review/new_states_v2/triage/decide.csv          22 rows that did not agree or had no date
  review/new_states_v2/triage/author_decisions.csv the author's decisions (and five rule-set Holi rows)
Output: review/new_states_v2/calendar_entries_2015_2025.csv in the column layout read by src/new_states_v1.py.
check_method says how each row was settled, so nothing is presented as checked one by one when it was not.
Run from the repository root: python src/new_states_v2_calendar_build_v1.py
"""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
T = ROOT/'review/new_states_v2/triage'
OUT = ROOT/'review/new_states_v2/calendar_entries_2015_2025.csv'
SCOPE = {'Bihar': ['Holi', 'Dussehra', 'Diwali'], 'Chhattisgarh': ['Holi', 'Dussehra', 'Diwali'],
         'Haryana': ['Holi', 'Dussehra', 'Diwali'], 'Punjab': ['Holi', 'Dussehra', 'Diwali'],
         'West Bengal': ['Holi', 'Dussehra', 'Diwali'], 'Kerala': ['Dussehra', 'Diwali'],
         'Odisha': ['Holi', 'Dussehra', 'Ganesh_Chaturthi', 'Diwali']}
YEARS = range(2015, 2026)
CHECK_DATE = '2026-11-15'


def main():
    m = pd.read_csv(T/'matched_all.csv', dtype=str).fillna('')
    k = pd.read_csv(T/'decide.csv', dtype=str).fillna('')
    a = pd.read_csv(T/'author_decisions.csv', dtype=str).fillna('')
    assert not a.basis.str.startswith('OPEN').any(), 'open rows remain'
    assert a.row.is_unique
    base = pd.concat([m.assign(triage='matched'), k.assign(triage='decide')], ignore_index=True)
    assert base.row.is_unique and len(base) == 231
    dec = a.set_index('row')
    rows = []
    for r in base.itertuples(index=False):
        date, by, method = r.date, 'triage (no person)', 'date agrees with an author-verified first-study date for the same family and year'
        if r.row in dec.index:
            d = dec.loc[r.row]
            date = d.final_date
            if d.basis.startswith('PROPOSED'):
                by, method = 'rule (not checked by the author)', 'Holi-day rule: later of two reference days, adopted after two spot-check errors'
            elif d.basis.startswith('author ok, no date entered'):
                by, method = 'Binay Verma', 'author ok; date set by the main-festival-day rule (author may veto)'
            else:
                by, method = 'Binay Verma', d.basis
        rows.append(dict(row=r.row, state=r.state, year=int(r.year), family=r.family, role='annual_as_issued_anchor', date=date,
                         label_in_document=r.label_in_document, not_listed_this_year=r.not_listed_this_year,
                         document_url=r.document_url, candidate_source=r.candidate_source, triage=r.triage,
                         triage_date=r.date, notes=r.notes, checked_by=by, check_date=CHECK_DATE, check_method=method))
    c = pd.DataFrame(rows).sort_values(['state', 'year', 'family']).reset_index(drop=True)
    # completeness and sanity
    want = {(s, y, f) for s, fs in SCOPE.items() for y in YEARS for f in fs}
    have = set(zip(c.state, c.year, c.family))
    assert have == want, (want - have, have - want)
    assert c.date.ne('').all()
    assert (pd.to_datetime(c.date).dt.year == c.year).all()
    c.to_csv(OUT, index=False)
    s = c.checked_by.value_counts().to_dict()
    print(OUT.relative_to(ROOT), len(c), s)
    print('changed from triage date:', int((c.date != c.triage_date).sum()))
    print('weekend anchors:', int(pd.to_datetime(c.date).dt.dayofweek.ge(5).sum()))


if __name__ == '__main__':
    main()
