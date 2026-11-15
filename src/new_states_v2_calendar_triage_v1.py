"""Triage of the machine-found calendar candidates for the second registered test (review/new_states_v2).
Festival days are mostly the same in every state, and review/new_states_v1/calendar_entries_2015_2025.csv holds 331 rows the
author verified for the first study. For each in-scope anchor row of the seven new states this script compares the candidate date
with the verified dates of the same family and year in the other states:
  match          candidate date equals the verified date (or one of them, if verified states differ)
  off_by_one     differs by one day from a verified date: needs a human look
  differs        differs by more than a day: needs a human look
  no_date        no candidate date (weekend or conflicting sources): needs a decision
Subsidiary (extra-day) rows are not used in this test (design choice, see DESIGN_DRAFT.md).
It writes review/new_states_v2/triage/ (decide.csv, spotcheck.csv, matched_all.csv, summary.json). The spot-check takes 3 matched
rows per state with numpy default_rng(20261115). Run from the repository root.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'review/new_states_v2/triage'
SCOPE = {'Bihar': ['Holi', 'Dussehra', 'Diwali'], 'Chhattisgarh': ['Holi', 'Dussehra', 'Diwali'], 'Haryana': ['Holi', 'Dussehra', 'Diwali'],
         'Kerala': ['Dussehra', 'Diwali'], 'Odisha': ['Holi', 'Dussehra', 'Ganesh_Chaturthi', 'Diwali'],
         'Punjab': ['Holi', 'Dussehra', 'Diwali'], 'West Bengal': ['Holi', 'Dussehra', 'Diwali']}


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    v = pd.read_csv(ROOT/'review/new_states_v1/calendar_entries_2015_2025.csv', dtype=str).fillna('')
    va = v[(v.role == 'annual_as_issued_anchor') & (v.date != '')]
    ref = va.groupby(['family', 'year']).date.agg(lambda s: sorted(set(s))).to_dict()
    d = pd.read_csv(ROOT/'review/new_states_v2/calendar_check_list_2015_2025.csv', dtype=str).fillna('')
    a = d[d.role == 'annual_as_issued_anchor'].copy()
    a = a[[f in SCOPE[s] for s, f in zip(a.state, a.family)]].copy()

    def cls(r):
        R = ref.get((r.family, r.year), [])
        if r.date == '':
            return 'no_date'
        if not R:
            return 'differs'
        if r.date in R:
            return 'match'
        dd = pd.Timestamp(r.date)
        return 'off_by_one' if any(abs((dd-pd.Timestamp(x)).days) == 1 for x in R) else 'differs'
    a['verified_dates_other_states'] = [';'.join(ref.get((f, y), [])) for f, y in zip(a.family, a.year)]
    a['comparison'] = a.apply(cls, axis=1)
    a['proposed_date'] = [(x.split(';')[0] if (c == 'no_date' and ';' not in x and x) else r)
                          for x, c, r in zip(a.verified_dates_other_states, a.comparison, a.date)]
    keep = ['row', 'state', 'year', 'family', 'comparison', 'date', 'verified_dates_other_states', 'proposed_date', 'candidate_source',
            'not_listed_this_year', 'label_in_document', 'document_url', 'quoted_line', 'notes']
    dec = a[a.comparison != 'match'][keep].sort_values(['comparison', 'state', 'year', 'family'])
    dec.to_csv(OUT/'decide.csv', index=False)
    m = a[a.comparison == 'match']
    m[keep].to_csv(OUT/'matched_all.csv', index=False)
    rng = np.random.default_rng(20261115)
    pick = []
    for st, g in m.groupby('state'):
        pick += list(rng.choice(g.index.values, size=3, replace=False))
    m.loc[pick, keep].sort_values(['state', 'year', 'family']).to_csv(OUT/'spotcheck.csv', index=False)
    (OUT/'summary.json').write_text(json.dumps(dict(in_scope_anchor_rows=len(a), by_comparison=a.comparison.value_counts().to_dict(),
                                                   by_state=pd.crosstab(a.state, a.comparison).to_dict('index')), indent=1))
    print(a.comparison.value_counts().to_dict(), len(dec), len(pick))


if __name__ == '__main__':
    main()
