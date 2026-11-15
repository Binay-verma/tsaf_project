"""Analysis of the leaf-size experiment against its pre-committed predictions (results/leaf_size_experiment_v1/PREDICTION.md)."""
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
E = ROOT/'results/leaf_size_experiment_v1'


def balanced(d):
    d = d.assign(MASE=(d.prediction-d.actual).abs()/d.mase_scale)
    s = d.groupby(['leaf', 'family', 'year', 'state', 'arm']).MASE.mean().unstack('arm')
    s['diff'] = s['day5']-s['pooled_day5']
    return s['diff'].groupby(['leaf', 'family', 'year']).mean().groupby('leaf').agg(['mean', 'count'])


def main():
    out = E/'analysis'; out.mkdir(exist_ok=False)
    res, rep = {}, {}
    rows = []
    for t in ['v1', 'v2']:
        d = pd.read_csv(E/t/'predictions.csv'); f = pd.read_json(E/t/'fits.json')
        key = ['state', 'family', 'year', 'origin', 'date']
        # reproduction checks
        reg2 = pd.read_csv(ROOT/f'results/new_states_{t}/event_window/lightgbm_capacity2/predictions.csv')
        regs = pd.read_csv(ROOT/f'results/new_states_{t}/event_window/lightgbm/predictions.csv')
        chk = {}
        for arm in ['calendar', 'day5', 'pooled_day5']:
            a = d[(d.leaf == 2) & (d.arm == arm)].merge(reg2[(reg2.horizon == 1) & (reg2.arm == arm)], on=key, suffixes=('', '_reg'))
            chk[f'leaf2_{arm}_max_abs_diff'] = float((a.prediction-a.prediction_reg).abs().max()); chk[f'leaf2_{arm}_n'] = len(a)
            sel = f[['state', 'year', 'selected_leaf']].drop_duplicates()
            b = d[d.arm == arm].merge(sel, on=['state', 'year'])
            b = b[b.leaf == b.selected_leaf].merge(regs[(regs.horizon == 1) & (regs.arm == arm)], on=key, suffixes=('', '_reg'))
            chk[f'selected_{arm}_max_abs_diff'] = float((b.prediction-b.prediction_reg).abs().max()); chk[f'selected_{arm}_n'] = len(b)
        rep[t] = chk
        # P1, P1b
        p1 = f[f.typed_max_count < f.leaf]
        p1b = f[f.typed_max_count < 3]
        share = f.groupby('leaf').agg(typed_equals_calendar=('typed_equals_calendar', 'mean'), pooled_equals_calendar=('pooled_equals_calendar', 'mean'),
                                     fits=('typed_equals_calendar', 'size'))
        act = reg2[(reg2.horizon == 1) & (reg2.arm == 'calendar')][key+['actual']]
        dd = d.merge(act, on=key, how='left'); assert len(dd) == len(d) and dd.actual.notna().all()
        bal = balanced(dd)
        res[t] = dict(
            P1=dict(fits=len(p1), equal=int(p1.typed_equals_calendar.sum()), held=bool(p1.typed_equals_calendar.all())),
            P1b=dict(fits=len(p1b), equal=int(p1b.typed_equals_calendar.sum()), held=bool(p1b.typed_equals_calendar.all())),
            P2=dict(share_by_leaf=share.typed_equals_calendar.round(3).to_dict(), held=bool(share.typed_equals_calendar.is_monotonic_increasing)),
            P3=dict(typed_minus_pooled_by_leaf=bal['mean'].round(5).to_dict(), held=bool((bal.loc[[2, 3, 4, 5, 6, 8, 10, 20], 'mean'] > 0).all())),
            P4=dict(pooled_equals_calendar_by_leaf=share.pooled_equals_calendar.round(3).to_dict(),
                    held=bool((share.loc[[1, 2, 3, 4, 5, 6], 'pooled_equals_calendar'] < 0.5).all())),
            typed_max_count_distribution=f.drop_duplicates(['state', 'year', 'refit']).typed_max_count.value_counts().sort_index().to_dict(),
            pooled_count_median=float(f.drop_duplicates(['state', 'year', 'refit']).pooled_count.median()))
        for L, r in share.iterrows():
            rows.append(dict(test=t, leaf=L, typed_equals_calendar_share=r.typed_equals_calendar, pooled_equals_calendar_share=r.pooled_equals_calendar,
                             typed_minus_pooled=bal.loc[L, 'mean'], clusters=int(bal.loc[L, 'count'])))
    pd.DataFrame(rows).to_csv(out/'by_leaf.csv', index=False)
    (out/'predictions_vs_results.json').write_text(json.dumps(dict(reproduction=rep, results=res), indent=1, default=str))
    print(json.dumps(dict(reproduction=rep, results=res), indent=1, default=str))


if __name__ == '__main__':
    main()
