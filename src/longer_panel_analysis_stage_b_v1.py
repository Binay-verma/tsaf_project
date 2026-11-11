"""Registered confirmatory analysis for Stage B (results/model_class_hypothesis_v1 on Maharashtra 2019-2021).

Run after the four local workers finish: python src/longer_panel_analysis_stage_b_v1.py
Writes only results/longer_panel_stage_b_v1/analysis/.
"""
import json
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from festival_feature_design import sha, dump
from cluster_inference_v1 import holm
from longer_panel_stage_b_v1 import OUT, MODELS, EVENT_YEARS

TESTS = {'H1': ('lightgbm', +1), 'H2': ('sarimax', -1), 'H1b (secondary)': ('lightgbm_capacity2', +1)}
ALPHA = 0.05


def load():
    parts = []
    for m in MODELS:
        run = json.loads((OUT/'event_window'/m/'run.json').read_text())
        assert sha(OUT/'event_window'/m/'predictions.csv') == run['predictions_sha256']
        parts.append(pd.read_csv(OUT/'event_window'/m/'predictions.csv'))
    d = pd.concat(parts, ignore_index=True)
    d['MASE'] = (d.prediction-d.actual).abs()/d.mase_scale
    return d


def clusters(d, years):
    x = d[d.year.isin(years)]
    return x.groupby(['model', 'arm', 'horizon', 'family', 'year']).MASE.mean()


def one_sided(v, direction):
    """Exact one-sided sign-flip p for the mean in the stated direction (direction*mean large)."""
    v = np.asarray(v, float)*direction; n = len(v)
    signs = (((np.arange(2**n)[:, None] >> np.arange(n)) & 1)*2-1).astype(np.int8)
    means = (signs@v)/n
    return float(np.mean(means >= v.mean()-1e-12))


def evaluate(d, years):
    c = clusters(d, years); rows = []
    for name, (m, direction) in TESTS.items():
        diff = (c[(m, 'day5', 1)]-c[(m, 'pooled_day5', 1)])
        assert len(diff) == 5*len(years)
        yv = {y: float(diff.xs(y, level='year').mean()) for y in years}
        rows.append(dict(hypothesis=name, model=m, expected_sign='+' if direction > 0 else '-', clusters=len(diff),
                         typed_minus_pooled=float(diff.mean()), **{f'year_{y}': v for y, v in yv.items()},
                         years_in_direction=int(sum(np.sign(v) == direction for v in yv.values())),
                         p_one_sided=one_sided(diff.values, direction)))
    r = pd.DataFrame(rows)
    prim = r.hypothesis.isin(['H1', 'H2'])
    r.loc[prim, 'holm'] = holm(r.loc[prim, 'p_one_sided'].values)
    need = 2 if len(years) == 3 else len(years)
    def decide(x):
        if np.sign(x.typed_minus_pooled) == -1*(1 if x.expected_sign == '+' else -1):
            return 'CONTRADICTED'
        p = x.holm if not np.isnan(x.get('holm', np.nan)) else x.p_one_sided
        return 'CONFIRMED' if (p < ALPHA and x.years_in_direction >= need) else 'NOT CONFIRMED'
    r['decision'] = r.apply(decide, axis=1)
    return r


def main():
    out = OUT/'analysis'
    if out.exists():
        raise FileExistsError('Analysis already written')
    d = load()
    main_r = evaluate(d, EVENT_YEARS); sens = evaluate(d, [2019, 2021])
    out.mkdir()
    main_r.to_csv(out/'hypothesis_tests.csv', index=False); sens.to_csv(out/'sensitivity_without_2020.csv', index=False)
    b = d.groupby(['model', 'arm', 'horizon', 'family', 'year']).MASE.mean().groupby(['model', 'arm', 'horizon', 'family']).mean().groupby(['model', 'arm', 'horizon']).mean()
    b.rename('MASE').reset_index().to_csv(out/'balanced.csv', index=False)
    s = dict(created_utc=datetime.now(timezone.utc).isoformat(),
             decisions={r.hypothesis: r.decision for r in main_r.itertuples()},
             sensitivity_without_2020={r.hypothesis: r.decision for r in sens.itertuples()},
             outputs={f.name: sha(f) for f in sorted(out.glob('*.csv'))})
    dump(out/'summary.json', s)
    print(main_r.round(5).to_string(index=False)); print(json.dumps(s, indent=1))


if __name__ == '__main__':
    main()
