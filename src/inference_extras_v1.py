"""Extra inference checks on the registered tests and the leaf-2 result (EXPLORATORY; written after all registered analyses).

1. Year-block sign-flip: the registered cluster tests treat family-year clusters as independent, although clusters in the
   same year share weather and data. Here each year mean is one unit and the one-sided p is exact over all 2^k sign
   assignments (k = number of event years).
2. Leave-one-state-out: the registered statistic recomputed without each state in turn.
3. Leaf-2 conditional: in the leaf-size experiment at L = 2, lead-1 typed minus pooled MASE (case-level mean) split by
   whether the fit could use the typed flags (typed forecasts differ from calendar forecasts) or not.
Writes results/inference_extras_v1/.
"""
import itertools
from pathlib import Path
import numpy as np
import pandas as pd
import scorecard_v1 as sc

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'results/inference_extras_v1'
KEY = ['state', 'family', 'year', 'origin', 'date']


def exact_year(c, direction):
    yv = c.groupby(level='year').mean().to_numpy()*direction
    obs = yv.mean()
    hits = sum(np.dot(s, yv)/len(yv) >= obs-1e-12 for s in itertools.product([1, -1], repeat=len(yv)))
    return hits/2**len(yv), len(yv)


def main():
    OUT.mkdir(exist_ok=False)
    rows = []
    for test, base, hyps in [('Stage B', 'results/longer_panel_stage_b_v1', [('H2', 'SARIMAX', 'sarimax', -1)]),
                             ('First test', 'results/new_states_v1', [('H1', 'SARIMAX', 'sarimax', -1), ('H3', 'Leaf-2 LightGBM', 'lightgbm_capacity2', 1)]),
                             ('Second test', 'results/new_states_v2', [('R1', 'SARIMAX', 'sarimax', -1), ('R2', 'Leaf-2 LightGBM', 'lightgbm_capacity2', 1)])]:
        for h, label, m, d in hyps:
            u = sc.load(base, 'event_window', m)
            c = u.groupby(['family', 'year'])['diff'].mean()
            p, k = exact_year(c, d)
            row = dict(test=test, hypothesis=h, model=label, estimate=c.mean(), year_block_p=p, years=k)
            if u.state.nunique() > 1:
                lo = {st: u[u.state != st].groupby(['family', 'year'])['diff'].mean().mean() for st in sorted(u.state.unique())}
                row.update(loso_min=min(lo.values()), loso_max=max(lo.values()),
                           loso_state_at_weakest=(min(lo, key=lo.get) if d > 0 else max(lo, key=lo.get)))
            rows.append(row)
    pd.DataFrame(rows).to_csv(OUT/'year_block_and_leave_one_state_out.csv', index=False)

    cond = []
    for t, base in [('first', 'results/new_states_v1'), ('second', 'results/new_states_v2')]:
        tag = 'v1' if t == 'first' else 'v2'
        f = pd.read_json(ROOT/f'results/leaf_size_experiment_v1/{tag}/fits.json'); f = f[f.leaf == 2]
        d = pd.read_csv(ROOT/f'results/leaf_size_experiment_v1/{tag}/predictions.csv'); d = d[d.leaf == 2]
        reg = pd.read_csv(ROOT/base/'event_window/lightgbm_capacity2/predictions.csv')
        d = d.merge(reg[(reg.horizon == 1) & (reg.arm == 'calendar')][KEY+['actual']], on=KEY)
        d['refit'] = pd.to_datetime(d.origin).dt.to_period('M').dt.start_time.dt.strftime('%Y-%m-%d')
        d = d.merge(f[['state', 'year', 'refit', 'typed_equals_calendar']], on=['state', 'year', 'refit'])
        d['MASE'] = (d.prediction-d.actual).abs()/d.mase_scale
        w = d.pivot_table(index=KEY+['typed_equals_calendar'], columns='arm', values='MASE').reset_index()
        for k, g in w.groupby('typed_equals_calendar'):
            cond.append(dict(test=t, fits='typed flags unusable' if k else 'typed flags usable', cases=len(g),
                             typed_minus_pooled=(g.day5-g.pooled_day5).mean(), calendar=g.calendar.mean(), typed=g.day5.mean(), pooled=g.pooled_day5.mean()))
    pd.DataFrame(cond).to_csv(OUT/'leaf2_by_typed_usability.csv', index=False)
    print(pd.DataFrame(rows).round(4).to_string(index=False)); print(pd.DataFrame(cond).round(4).to_string(index=False))


if __name__ == '__main__':
    main()
