"""Exploratory analysis for results/longer_panel_foundation_v1 (Chronos-2, TimesFM-3 over 2022-2025).

Run after the six Colab workers finish: python src/longer_panel_foundation_analysis_v1.py
Writes only results/longer_panel_foundation_v1/analysis/.
"""
import json
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from forecasting import ROOT
from festival_feature_design import sha, dump
from cluster_inference_v1 import holm
from longer_panel_analysis_stage_a_v1 import balanced, clusters, sign_flip, REPS
from longer_panel_foundation_v1 import OUT, MODELS, COHORTS, ALL_ARMS

STORED = ROOT/'results/calendar_recenter_recovery_v1/analysis/breadth'
KEY = ['family', 'state', 'year', 'date', 'horizon', 'arm']
YEARS = [2022, 2023, 2024, 2025]


def new(cohort):
    parts = []
    for m in MODELS:
        run = json.loads((OUT/cohort/m/'run.json').read_text())
        assert sha(OUT/cohort/m/'predictions.csv') == run['predictions_sha256']
        parts.append(pd.read_csv(OUT/cohort/m/'predictions.csv'))
    return pd.concat(parts, ignore_index=True)


def stored(cohort):
    d = pd.read_csv(STORED/cohort/'predictions_compared.csv')
    return d[d.version.eq('document_aligned') & d.model.isin(MODELS)].drop(columns=['version', 'MAE_GWh', 'MASE'])


def reproduction():
    r = new('reproduce_2024'); s = stored('event_window')
    m = r.merge(s, on=KEY+['model'], suffixes=('', '_stored'))
    assert len(m) == len(r)
    ok = np.isclose(m.prediction, m.prediction_stored, rtol=2e-4, atol=1e-3)
    return dict(rows=len(m), within_tolerance=int(ok.sum()), max_abs_difference=float((m.prediction-m.prediction_stored).abs().max()),
                passed=bool(ok.all()))


def combined(cohort_new, cohort_stored):
    d = pd.concat([new(cohort_new), stored(cohort_stored)[lambda x: x.year.isin([2024, 2025])]], ignore_index=True)
    d['MASE'] = (d.prediction-d.actual).abs()/d.mase_scale
    assert sorted(d.year.unique()) == YEARS and set(d.arm) == set(ALL_ARMS)
    return d


def main():
    out = OUT/'analysis'
    if out.exists():
        raise FileExistsError('Analysis already written')
    rep = reproduction()
    out.mkdir()
    dump(out/'reproduction.json', rep)
    if not rep['passed']:
        print('Reference arms outside tolerance; 2022-2023 forecasts are not combined with stored 2024-2025 ones.', rep)
        return
    ev = combined('event_2022_2023', 'event_window'); od = combined('ordinary_2022_2023', 'ordinary')
    B = balanced(ev); C = clusters(ev); rows = []
    for m in MODELS:
        for rp, (t, p) in REPS.items():
            for h in [1, 7, 14]:
                diff = C[(m, t, h)]-C[(m, p, h)]
                assert len(diff) == 20
                pval, n = sign_flip(diff.values)
                yv = {y: balanced(ev, years=[y])[(m, t, h)]-balanced(ev, years=[y])[(m, p, h)] for y in YEARS}
                full = B[(m, t, h)]-B[(m, p, h)]
                rows.append(dict(model=m, representation=rp, lead=h, typed=B[(m, t, h)], pooled=B[(m, p, h)], typed_minus_pooled=full,
                                 **{f'year_{y}': v for y, v in yv.items()},
                                 years_same_sign=int(sum(np.sign(v) == np.sign(full) and v != 0 for v in yv.values())),
                                 clusters=20, p_signflip=pval))
    r = pd.DataFrame(rows)
    prim = r.lead.eq(1)
    r.loc[prim, 'holm_primary'] = holm(r.loc[prim, 'p_signflip'].values)
    r['supported'] = prim & (r.holm_primary < 0.05) & (r.years_same_sign >= 3)
    r.to_csv(out/'typed_vs_pooled.csv', index=False)
    B.rename('MASE').reset_index().to_csv(out/'event_balanced.csv', index=False)
    balanced(od).rename('MASE').reset_index().to_csv(out/'ordinary_balanced.csv', index=False)
    pd.DataFrame([dict(model=m, lead=h, **{a: B[(m, a, h)] for a in ALL_ARMS}) for m in MODELS for h in [1, 7, 14]]).to_csv(out/'controls.csv', index=False)
    s = dict(created_utc=datetime.now(timezone.utc).isoformat(), status='exploratory', reproduction=rep,
             supported=r[r.supported][['model', 'representation', 'lead', 'typed_minus_pooled']].to_dict('records'),
             lead1_day=r[prim & r.representation.eq('day')][['model', 'typed_minus_pooled', 'p_signflip', 'holm_primary', 'years_same_sign']].to_dict('records'),
             outputs={f.name: sha(f) for f in sorted(out.glob('*.csv'))})
    dump(out/'summary.json', s)
    print(r.round(4).to_string(index=False)); print(json.dumps(s, indent=1, default=str))


if __name__ == '__main__':
    main()
