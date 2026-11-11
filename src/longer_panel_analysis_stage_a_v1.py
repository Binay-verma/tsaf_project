"""Registered analysis for results/longer_panel_stage_a_v1 (see each cohort's protocol.json).

Run after all four local workers have finished for both cohorts:
  python src/longer_panel_analysis_stage_a_v1.py
Writes only results/longer_panel_stage_a_v1/analysis/.
"""
import json
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from forecasting import ROOT
from festival_feature_design import sha, dump
from cluster_inference_v1 import holm
from longer_panel_stage_a_v1 import OUT, MODELS, EVENT_YEARS

REPS = {'day': ('day5', 'pooled_day5'), 'window': ('window5', 'pooled_window5')}
ALPHA = 0.05


def load(cohort):
    parts = []
    for m in MODELS:
        run = json.loads((OUT/cohort/m/'run.json').read_text())
        assert sha(OUT/cohort/m/'predictions.csv') == run['predictions_sha256']
        parts.append(pd.read_csv(OUT/cohort/m/'predictions.csv'))
    d = pd.concat(parts, ignore_index=True)
    d['MASE'] = (d.prediction-d.actual).abs()/d.mase_scale
    return d


def clusters(d):
    s = d.groupby(['model', 'arm', 'horizon', 'family', 'year', 'state']).MASE.mean()
    return s.groupby(['model', 'arm', 'horizon', 'family', 'year']).mean()


def balanced(d, years=None, families=None):
    x = d if years is None else d[d.year.isin(years)]
    x = x if families is None else x[x.family.isin(families)]
    c = clusters(x)
    return c.groupby(['model', 'arm', 'horizon', 'family']).mean().groupby(['model', 'arm', 'horizon']).mean()


_SIGNS = {}


def sign_flip(v):
    v = np.asarray(v, float); n = len(v)
    if n not in _SIGNS:
        _SIGNS[n] = (((np.arange(2**n)[:, None] >> np.arange(n)) & 1)*2-1).astype(np.int8)
    means = np.abs(_SIGNS[n]@v)/n
    return float(np.mean(means >= abs(v.mean())-1e-12)), 2**n


def main():
    out = OUT/'analysis'
    if out.exists():
        raise FileExistsError('Analysis already written')
    ev = load('event_window'); od = load('ordinary')
    assert sorted(ev.year.unique()) == EVENT_YEARS
    B = balanced(ev); C = clusters(ev)
    fams = sorted(ev.family.unique())
    rows = []
    for m in MODELS:
        for rep, (t, p) in REPS.items():
            for h in [1, 7, 14]:
                diff = (C[(m, t, h)]-C[(m, p, h)])
                assert len(diff) == 20
                pval, n = sign_flip(diff.values)
                yv = {y: balanced(ev, years=[y])[(m, t, h)]-balanced(ev, years=[y])[(m, p, h)] for y in EVENT_YEARS}
                lofo = [balanced(ev, families=[f for f in fams if f != x])[(m, t, h)]-balanced(ev, families=[f for f in fams if f != x])[(m, p, h)] for x in fams]
                full = B[(m, t, h)]-B[(m, p, h)]
                old = balanced(ev, years=[2024, 2025]); new = balanced(ev, years=[2022, 2023])
                rows.append(dict(model=m, representation=rep, lead=h, typed=B[(m, t, h)], pooled=B[(m, p, h)], typed_minus_pooled=full,
                                 **{f'year_{y}': v for y, v in yv.items()}, years_same_sign=int(sum(np.sign(v) == np.sign(full) and v != 0 for v in yv.values())),
                                 lofo_min=min(lofo), lofo_max=max(lofo), lofo_sign_flips=int(sum(np.sign(v) != np.sign(full) for v in lofo)),
                                 new_years=new[(m, t, h)]-new[(m, p, h)], old_years=old[(m, t, h)]-old[(m, p, h)],
                                 clusters=20, p_signflip=pval, assignments=n))
    r = pd.DataFrame(rows)
    prim = r.lead.eq(1)
    r.loc[prim, 'holm_primary'] = holm(r.loc[prim, 'p_signflip'].values)
    r['holm_all24'] = holm(r.p_signflip.values)
    r['supported'] = prim & (r.holm_primary < ALPHA) & (r.years_same_sign >= 3)
    out.mkdir()
    r.to_csv(out/'typed_vs_pooled.csv', index=False)
    B.rename('MASE').reset_index().to_csv(out/'event_balanced.csv', index=False)
    balanced(od).rename('MASE').reset_index().to_csv(out/'ordinary_balanced.csv', index=False)
    ctl = []
    for m in MODELS:
        for h in [1, 7, 14]:
            ctl.append(dict(model=m, lead=h, **{a: B[(m, a, h)] for a in ['calendar', 'zero5', 'placebo_day5', 'placebo_window5', 'day5', 'pooled_day5', 'window5', 'pooled_window5']}))
    pd.DataFrame(ctl).to_csv(out/'controls.csv', index=False)
    dec = []
    for m in MODELS:
        for rep, (t, p) in REPS.items():
            for h in [1, 7, 14]:
                for y in [2023, 2024, 2025]:
                    prev = balanced(ev, years=[y-1]); cur = balanced(ev, years=[y])
                    pick = t if prev[(m, t, h)] < prev[(m, p, h)] else p
                    cy = ev[ev.year.eq(y) & ev.model.eq(m) & ev.horizon.eq(h)]
                    a = cy[cy.arm.eq(t)].set_index(['family', 'state', 'date']); b = cy[cy.arm.eq(p)].set_index(['family', 'state', 'date']).reindex(a.index)
                    avg = a.assign(MASE=((a.prediction+b.prediction)/2-a.actual).abs()/a.mase_scale, arm='avg').reset_index()
                    avg_b = balanced(avg.assign(model=m, horizon=h))[(m, 'avg', h)]
                    oracle = min(cur[(m, t, h)], cur[(m, p, h)])
                    dec.append(dict(model=m, representation=rep, lead=h, year=y, follow_regret=cur[(m, pick, h)]-oracle,
                                    average_regret=avg_b-oracle, typed_regret=cur[(m, t, h)]-oracle, pooled_regret=cur[(m, p, h)]-oracle))
    dd = pd.DataFrame(dec); dd.to_csv(out/'decision_rules.csv', index=False)
    summary = dict(created_utc=datetime.now(timezone.utc).isoformat(),
                   primary_cells=int(prim.sum()), primary_holm_below_005=int((r.loc[prim, 'holm_primary'] < ALPHA).sum()),
                   supported=r[r.supported][['model', 'representation', 'lead', 'typed_minus_pooled']].to_dict('records'),
                   all24_raw_below_005=int((r.p_signflip < ALPHA).sum()), all24_holm_below_005=int((r.holm_all24 < ALPHA).sum()),
                   smallest_attainable_p=2/2**20,
                   follow_picked_worse=int((dd.follow_regret > 0).sum()), decision_cells=len(dd),
                   mean_regret=dict(follow=float(dd.follow_regret.mean()), average=float(dd.average_regret.mean()),
                                    typed=float(dd.typed_regret.mean()), pooled=float(dd.pooled_regret.mean())),
                   max_regret=dict(follow=float(dd.follow_regret.max()), average=float(dd.average_regret.max()),
                                   typed=float(dd.typed_regret.max()), pooled=float(dd.pooled_regret.max())),
                   outputs={f.name: sha(f) for f in sorted(out.glob('*.csv'))})
    dump(out/'summary.json', summary)
    print(json.dumps(summary, indent=1, default=str))


if __name__ == '__main__':
    main()
