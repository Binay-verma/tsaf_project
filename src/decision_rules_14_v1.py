"""Decision rules on the 14 new states of both registered tests (EXPLORATORY; stored forecasts only).

Rules: always typed, always pooled, equal-weight average of the typed and pooled point forecasts, and follow last
year's winner (the representation with the lower balanced MASE in the previous event year). Cell = test x local
model x lead x event year with a previous year (2018-2025). Balanced MASE as registered (state-family-year, then
states within family-year, then family-years within year). Regret = rule MASE minus the hindsight-better of typed
and pooled in that cell. Writes results/decision_rules_14_v1/.
"""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'results/decision_rules_14_v1'
MODELS = ['ridge', 'lightgbm', 'lightgbm_capacity2', 'sarimax']


def yearly(base, model):
    p = pd.read_csv(ROOT/base/'event_window'/model/'predictions.csv')
    p = p[p.arm.isin(['day5', 'pooled_day5'])]
    w = p.pivot_table(index=['family', 'year', 'state', 'date', 'horizon', 'origin', 'actual', 'mase_scale'], columns='arm', values='prediction').reset_index()
    w['average'] = (w.day5+w.pooled_day5)/2
    out = []
    for arm in ['day5', 'pooled_day5', 'average']:
        e = w.assign(MASE=(w[arm]-w.actual).abs()/w.mase_scale)
        b = e.groupby(['horizon', 'year', 'family', 'state']).MASE.mean().groupby(['horizon', 'year', 'family']).mean().groupby(['horizon', 'year']).mean()
        out.append(b.rename(arm))
    return pd.concat(out, axis=1).reset_index()


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    rows = []
    for test, base in [('first', 'results/new_states_v1'), ('second', 'results/new_states_v2')]:
        for m in MODELS:
            y = yearly(base, m)
            for h, g in y.groupby('horizon'):
                g = g.sort_values('year').reset_index(drop=True)
                for i in range(1, len(g)):
                    prev, cur = g.iloc[i-1], g.iloc[i]
                    best = min(cur.day5, cur.pooled_day5)
                    follow = cur.day5 if prev.day5 <= prev.pooled_day5 else cur.pooled_day5
                    rows.append(dict(test=test, model=m, horizon=int(h), year=int(cur.year), typed=cur.day5-best, pooled=cur.pooled_day5-best,
                                     average=cur.average-best, follow=follow-best, follow_picked_worse=bool(follow > best)))
    d = pd.DataFrame(rows)
    d.to_csv(OUT/'cells.csv', index=False)
    s = pd.DataFrame({r: dict(mean_regret=d[r].mean(), largest_regret=d[r].max()) for r in ['typed', 'pooled', 'follow', 'average']}).T
    s['cells'] = len(d); s['follow_picked_worse_cells'] = int(d.follow_picked_worse.sum())
    s.to_csv(OUT/'summary.csv')
    print(s.round(4).to_string())


if __name__ == '__main__':
    main()
