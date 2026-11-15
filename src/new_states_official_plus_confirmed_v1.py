"""Official plus provisionally confirmed calendar rows, and the same states with all rows (EXPLORATORY; after the registered
analysis). Reproduces results/new_states_v1_official_plus_confirmed (first computed interactively on 15 November 2026) with
the registered load/evaluate functions of src/new_states_analysis_v1.py. Writes to the folder given as the first argument
(default results/new_states_v1_official_plus_confirmed_rerun), never over the original.
  tests.csv: officially sourced rows plus rows the 2026-11-15 search matched to a copy of the government order (status match);
             a state-family-year cell is added back only when every non-official row of that cell was matched.
  by_state_group_all_rows.csv: the southern (AP, TS, TN) and the other four states, all rows regardless of source.
"""
import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
import new_states_analysis_v1 as na  # noqa: E402

SEARCH = ROOT/'review/new_states_v1/official_source_search_2026-11-15'
SOUTH = ['Andhra Pradesh', 'Telangana', 'Tamil Nadu']
OTHER = ['Uttar Pradesh', 'Rajasthan', 'Madhya Pradesh', 'Gujarat']


def main(out):
    out.mkdir(parents=True, exist_ok=False)
    d = na.load()
    cal = pd.read_csv(ROOT/'review/new_states_v1/calendar_entries_2015_2025.csv', dtype=str).fillna('')
    weak = cal[~cal.candidate_source.str.lower().str.match(r'(official|government reproduction)')].copy()
    weak['year'] = weak.year.astype(int)
    found = pd.concat([pd.read_csv(f, dtype=str).fillna('') for f in sorted(SEARCH.glob('found_*.csv'))])
    found['year'] = found.year.astype(int)
    ok = found[found.status == 'match'][['state', 'family', 'year', 'our_date']].rename(columns={'our_date': 'date'})
    weak = weak.merge(ok.assign(matched=True), on=['state', 'family', 'year', 'date'], how='left')
    weak['matched'] = weak['matched'].eq(True)
    still_weak = weak.groupby(['state', 'family', 'year']).matched.all().reset_index().query('~matched')[['state', 'family', 'year']]
    keys = d[['state', 'family', 'year']].drop_duplicates()
    keep = keys.merge(still_weak, how='left', indicator=True).query('_merge == "left_only"').drop(columns='_merge')
    keep = keep[keep.year.isin(na.EVENT_YEARS)].sort_values(['state', 'year', 'family'])
    keep.to_csv(out/'cells_kept.csv', index=False)
    na.evaluate(d, keep=keep).to_csv(out/'tests.csv', index=False)
    rows = []
    for name, states in [('AP+TS+TN, all rows', SOUTH), ('UP+RJ+MP+GJ, all rows', OTHER)]:
        rows.append(na.evaluate(d, keep=keys[keys.state.isin(states)]).assign(subset=name))
    g = pd.concat(rows)
    g[['subset'] + [c for c in g.columns if c != 'subset']].to_csv(out/'by_state_group_all_rows.csv', index=False)


if __name__ == '__main__':
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT/'results/new_states_v1_official_plus_confirmed_rerun')
