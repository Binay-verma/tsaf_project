"""Analysis of the robustness experiments against their pre-committed predictions (results/robustness_experiments_v1/PREDICTION.md)."""
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
E = ROOT/'results/robustness_experiments_v1'
KEY = ['state', 'family', 'year', 'origin', 'date']


def actuals(t):
    r = pd.read_csv(ROOT/f'results/new_states_{t}/event_window/ridge/predictions.csv')
    return r[(r.horizon == 1) & (r.arm == 'calendar')][KEY+['actual']]


def balanced(d, by):
    d = d.assign(MASE=(d.prediction-d.actual).abs()/d.mase_scale)
    s = d.groupby(by+['family', 'year', 'state', 'arm']).MASE.mean()
    return s.groupby(by+['family', 'year', 'arm']).mean().groupby(by+['arm']).mean().unstack('arm')


def registered(t, years):
    out = {}
    for m, f in [('ridge', 'ridge'), ('lgbm_leaf2', 'lightgbm_capacity2')]:
        p = pd.read_csv(ROOT/f'results/new_states_{t}/event_window/{f}/predictions.csv')
        p = p[(p.horizon == 1) & p.year.isin(years) & p.arm.isin(['day5', 'pooled_day5'])].assign(model=m)
        b = balanced(p, ['model'])
        out[m] = float(b['day5'].iloc[0]-b['pooled_day5'].iloc[0])
    return out


def main():
    out = E/'analysis'; out.mkdir(exist_ok=False)
    res = {}
    win_rows, hyb_rows, noise_rows, alpha_rows = [], [], [], []
    for t in ['v1', 'v2']:
        act = actuals(t)
        # window
        d = pd.read_csv(E/t/'window/predictions.csv').merge(act, on=KEY, how='left'); assert d.actual.notna().all()
        b = balanced(d, ['W', 'model'])
        for (W, m), r in b.iterrows():
            win_rows.append(dict(test=t, W=W, model=m, typed_minus_pooled=r.day5-r.pooled_day5, calendar=r.calendar, typed=r.day5, pooled=r.pooled_day5, hybrid=r.hybrid,
                                 hybrid_minus_best=r.hybrid-min(r.day5, r.pooled_day5)))
        sel = d[d.model == 'lgbm_selected'].pivot_table(index=['W', 'state', 'year', 'origin', 'family', 'date'], columns='arm', values='prediction')
        eq = (sel['day5'] == sel['calendar']).groupby(level=['W', 'state', 'year']).all().groupby(level='W').mean()
        res.setdefault(t, {})['window_selected_typed_equals_calendar_share_by_W'] = eq.round(3).to_dict()
        # noise
        n = pd.read_csv(E/t/'noise/predictions.csv').merge(act, on=KEY, how='left'); assert n.actual.notna().all()
        bn = balanced(n, ['ledger', 'model'])
        reg = registered(t, range(2017, 2026))
        for (led, m), r in bn.iterrows():
            noise_rows.append(dict(test=t, ledger=led, model=m, typed_minus_pooled=r.day5-r.pooled_day5, registered_typed_minus_pooled=reg[m],
                                   change=r.day5-r.pooled_day5-reg[m]))
        # alpha
        a = pd.read_csv(E/t/'ridge_alpha/predictions.csv').merge(act, on=KEY, how='left'); assert a.actual.notna().all()
        ba = balanced(a, ['model'])
        for m, r in ba.iterrows():
            alpha_rows.append(dict(test=t, alpha=float(m[len('ridge_alpha'):]), typed_minus_pooled=r.day5-r.pooled_day5, calendar=r.calendar, typed=r.day5,
                                   pooled=r.pooled_day5, hybrid=r.hybrid))
    W = pd.DataFrame(win_rows); N = pd.DataFrame(noise_rows); A = pd.DataFrame(alpha_rows)
    W.to_csv(out/'window.csv', index=False); N.to_csv(out/'noise.csv', index=False); A.to_csv(out/'ridge_alpha.csv', index=False)

    def decreasing(t, m):
        v = W[(W.test == t) & (W.model == m)].sort_values('W').typed_minus_pooled.to_numpy()
        return bool(np.all(np.diff(v) < 0))
    pred = {}
    pred['W1'] = {t: decreasing(t, 'lgbm_leaf2') for t in ['v1', 'v2']}
    pred['W2'] = {t: dict(decreasing=decreasing(t, 'lgbm_selected'), typed_used_at_2190=res[t]['window_selected_typed_equals_calendar_share_by_W'].get(2190, 1) < 1) for t in ['v1', 'v2']}
    pred['W3'] = {t: decreasing(t, 'ridge') for t in ['v1', 'v2']}
    h = W[W.W == 730]
    pred['H1'] = {t: bool(abs(h[(h.test == t) & (h.model == 'ridge')].hybrid_minus_best.iloc[0]) <= 0.005) for t in ['v1', 'v2']}
    pred['H2'] = {t: bool(abs(h[(h.test == t) & (h.model == 'lgbm_leaf2')].hybrid.iloc[0]-h[(h.test == t) & (h.model == 'lgbm_leaf2')].pooled.iloc[0])
                          < abs(h[(h.test == t) & (h.model == 'lgbm_leaf2')].hybrid.iloc[0]-h[(h.test == t) & (h.model == 'lgbm_leaf2')].typed.iloc[0])) for t in ['v1', 'v2']}
    pred['N1'] = {f'{r.test} {r.ledger} {r.model}': bool(r.change > 0) for r in N.itertuples()}
    pred['A1'] = {t: bool(len(set(np.sign(A[(A.test == t) & A.alpha.isin([0.1, 1, 10, 100])].typed_minus_pooled))) == 1) for t in ['v1', 'v2']}
    (out/'predictions_vs_results.json').write_text(json.dumps(dict(predictions=pred, extra=res), indent=1, default=str))
    pd.set_option('display.width', 200)
    print(W.round(4).to_string(index=False)); print(N.round(4).to_string(index=False)); print(A.round(4).to_string(index=False))
    print(json.dumps(dict(predictions=pred, extra=res), indent=1, default=str))


if __name__ == '__main__':
    main()
