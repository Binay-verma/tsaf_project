"""Merge machine-found candidate calendar rows for the new-states study into one file for the author's check.

No forecasting, no outcomes. Applies the conventions in review/new_states_v1/DESIGN_DRAFT.md and writes
review/new_states_v1/calendar_entries_2015_2025.csv (checked_by/check_date empty) plus a flag per row that tells the
author what to look at. Run from the repository root: python src/new_states_calendar_merge_v1.py
"""
import glob
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D = ROOT/'review/new_states_v1'
SCOPE = {'Andhra Pradesh': ['Holi', 'Ugadi_Gudi_Padwa', 'Ganesh_Chaturthi', 'Dussehra', 'Diwali'],
         'Telangana': ['Holi', 'Ugadi_Gudi_Padwa', 'Ganesh_Chaturthi', 'Dussehra', 'Diwali'],
         'Tamil Nadu': ['Ugadi_Gudi_Padwa', 'Ganesh_Chaturthi', 'Dussehra', 'Diwali'],
         'Madhya Pradesh': ['Holi', 'Ugadi_Gudi_Padwa', 'Dussehra', 'Diwali'],
         'Gujarat': ['Holi', 'Dussehra', 'Diwali'], 'Rajasthan': ['Holi', 'Dussehra', 'Diwali'],
         'Uttar Pradesh': ['Holi', 'Dussehra', 'Diwali']}
# Convention 1 (festival day vs substitute holiday): substitutes identified while sourcing, moved back to the festival day.
SUBSTITUTE = {('Madhya Pradesh', 2020, 'Dussehra', 'annual_as_issued_anchor'): ('2020-10-25', 'festival day Sunday 25 Oct; 26 Oct was a substitute holiday'),
              ('Andhra Pradesh', 2023, 'Diwali', 'annual_as_issued_anchor'): ('2023-11-12', 'festival day Sunday 12 Nov; 13 Nov was a substitute holiday')}
AMEND_WORDS = ['amend', 'moved', 'shift', 'changed', 'revised', 'added', 'substitut']


def main():
    d = pd.concat([pd.read_csv(f, dtype=str).fillna('') for f in sorted(glob.glob(str(D/'candidates_*.csv')))], ignore_index=True)
    d['year'] = d.year.astype(int)
    d['in_scope'] = [f in SCOPE[s] for s, f in zip(d.state, d.family)]
    d['flag'] = ''
    for k, (new, why) in SUBSTITUTE.items():
        m = (d.state == k[0]) & (d.year == k[1]) & (d.family == k[2]) & (d.role == k[3])
        assert m.sum() == 1, k
        d.loc[m, 'notes'] = d.loc[m, 'notes'] + f' | MERGE: anchor set to festival day {new} (was {d.loc[m, "date"].iloc[0]}): {why}.'
        d.loc[m, 'date'] = new
        d.loc[m, 'flag'] += 'substitute moved to festival day; '
    src = d.candidate_source.str.lower()
    notes = d.notes.str.lower()
    d.loc[src.str.startswith('repost') | (src == ''), 'flag'] += 'website source only - open the official document if you can; '
    d.loc[notes.str.contains('|'.join(AMEND_WORDS)), 'flag'] += 'amendment or extra day mentioned - confirm the festival day; '
    d.loc[notes.str.contains('weekend|sunday'), 'flag'] += 'weekend case; '
    d.loc[notes.str.contains('conflict|disagree|vs |differs|low confidence|unverified|typo|not found'), 'flag'] += 'sources conflict or unverified; '
    d.loc[d.in_scope & (d.role == 'annual_as_issued_anchor') & (d.date == ''), 'flag'] += 'in-scope family without a date this year (no flag, no cases unless you find one); '
    d['entered_by'] = 'Claude (machine-found)'
    d['checked_by'] = ''
    d['check_date'] = ''
    out = d[d.in_scope].drop(columns=['in_scope']).sort_values(['state', 'year', 'family', 'role']).reset_index(drop=True)
    out.insert(0, 'row', range(1, len(out)+1))
    out.to_csv(D/'calendar_entries_2015_2025.csv', index=False)
    d[~d.in_scope].to_csv(D/'out_of_scope_rows.csv', index=False)
    print(len(out), 'in-scope rows;', (out.flag == '').sum(), 'unflagged;', out.groupby('state').size().to_dict())


if __name__ == '__main__':
    main()
