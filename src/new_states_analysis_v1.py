"""Registered confirmatory analysis for results/new_states_v1 (written and committed before any forecast).

Run after the local workers and both foundation cohorts finish: python src/new_states_analysis_v1.py
Writes only results/new_states_v1/analysis/.
"""
import json
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from festival_feature_design import sha, dump
from cluster_inference_v1 import holm

ROOT = __import__('pathlib').Path(__file__).resolve().parents[1]
OUT = ROOT/'results/new_states_v1'
HYP = {'H1': ('sarimax', -1), 'H2': ('timesfm', +1), 'H3': ('lightgbm_capacity2', +1)}
REPORTED = ['ridge', 'lightgbm', 'chronos']
DRAWS, SEED, ALPHA, NEED_YEARS = 1_000_000, 20261113, 0.05, 6
EVENT_YEARS = list(range(2017, 2026))


def load():
    parts = []
    for cohort, models in [('event_window', ['ridge', 'lightgbm', 'lightgbm_capacity2', 'sarimax']),
                           ('fm_2017_2020', ['chronos', 'timesfm']), ('fm_2021_2025', ['chronos', 'timesfm'])]:
        for m in models:
            run = json.loads((OUT/cohort/m/'run.json').read_text())
            assert sha(OUT/cohort/m/'predictions.csv') == run['predictions_sha256']
            parts.append(pd.read_csv(OUT/cohort/m/'predictions.csv'))
    d = pd.concat(parts, ignore_index=True)
    d['MASE'] = (d.prediction-d.actual).abs()/d.mase_scale
    return d


def clusters(d, model, years=EVENT_YEARS, keep=None):
    """Family-year cluster values of typed-day minus pooled-day lead-1 MASE (equal weight over states)."""
    x = d[(d.model == model) & (d.horizon == 1) & d.year.isin(years) & d.arm.isin(['day5', 'pooled_day5'])]
    if keep is not None:
        x = x.merge(keep, on=['state', 'family', 'year'])
    s = x.groupby(['family', 'year', 'state', 'arm']).MASE.mean().unstack('arm')
    s = (s['day5']-s['pooled_day5']).rename('diff')
    return s.groupby(['family', 'year']).mean()


def signflip(v, direction, draws=DRAWS, seed=SEED):
    v = np.asarray(v, float)*direction
    rng = np.random.default_rng(seed)
    obs = v.mean(); k = 0
    for start in range(0, draws, 100_000):
        n = min(100_000, draws-start)
        signs = rng.integers(0, 2, size=(n, len(v)), dtype=np.int8)*2-1
        k += int(((signs@v)/len(v) >= obs-1e-12).sum())
    return (k+1)/(draws+1)


def evaluate(d, years=EVENT_YEARS, keep=None):
    rows = []
    for h, (m, direction) in HYP.items():
        c = clusters(d, m, years, keep)
        yv = c.groupby(level='year').mean()
        rows.append(dict(hypothesis=h, model=m, expected_sign='+' if direction > 0 else '-', clusters=len(c), states_per_cluster=None,
                         typed_minus_pooled=float(c.mean()), years_in_direction=int((np.sign(yv) == direction).sum()), years=len(yv),
                         p_one_sided=signflip(c.values, direction), p_opposite=signflip(c.values, -direction),
                         **{f'year_{y}': float(v) for y, v in yv.items()}))
    r = pd.DataFrame(rows)
    r['holm'] = holm(r.p_one_sided.values)
    need = NEED_YEARS if len(years) == 9 else int(np.ceil(2*len(years)/3))

    def decide(x):
        if np.sign(x.typed_minus_pooled) == -1*(1 if x.expected_sign == '+' else -1) and x.p_opposite < ALPHA:
            return 'CONTRADICTED'
        return 'CONFIRMED' if (x.holm < ALPHA and x.years_in_direction >= need) else 'NOT CONFIRMED'
    r['decision'] = r.apply(decide, axis=1)
    return r


def main():
    out = OUT/'analysis'
    if out.exists():
        raise FileExistsError('Analysis already written')
    d = load()
    main_r = evaluate(d)
    no_covid = evaluate(d, [y for y in EVENT_YEARS if y not in (2020, 2021)])
    cal = pd.read_csv(ROOT/'review/new_states_v1/calendar_entries_2015_2025.csv', dtype=str).fillna('')
    weak = cal[~cal.candidate_source.str.lower().str.match(r'(official|government reproduction)')]
    keep = d[['state', 'family', 'year']].drop_duplicates()
    weak_keys = weak[['state', 'family', 'year']].assign(year=lambda x: x.year.astype(int)).drop_duplicates()
    keep = keep.merge(weak_keys, how='left', indicator=True).query('_merge == "left_only"').drop(columns='_merge')
    official = evaluate(d, keep=keep)
    out.mkdir()
    main_r.to_csv(out/'hypothesis_tests.csv', index=False)
    no_covid.to_csv(out/'sensitivity_without_2020_2021.csv', index=False)
    official.to_csv(out/'sensitivity_official_sources_only.csv', index=False)
    rep = []
    for m in REPORTED+[v[0] for v in HYP.values()]:
        c = clusters(d, m)
        rep.append(dict(model=m, typed_minus_pooled=float(c.mean()), clusters=len(c), p_two_sided=min(1, 2*min(signflip(c.values, 1), signflip(c.values, -1)))))
    pd.DataFrame(rep).to_csv(out/'all_models_lead1.csv', index=False)
    b = d.groupby(['model', 'arm', 'horizon', 'family', 'year', 'state']).MASE.mean().groupby(['model', 'arm', 'horizon', 'family', 'year']).mean() \
         .groupby(['model', 'arm', 'horizon', 'family']).mean().groupby(['model', 'arm', 'horizon']).mean()
    b.rename('MASE').reset_index().to_csv(out/'balanced.csv', index=False)
    s = dict(created_utc=datetime.now(timezone.utc).isoformat(),
             decisions={r.hypothesis: r.decision for r in main_r.itertuples()},
             sensitivity_without_2020_2021={r.hypothesis: r.decision for r in no_covid.itertuples()},
             sensitivity_official_sources_only={r.hypothesis: r.decision for r in official.itertuples()},
             outputs={f.name: sha(f) for f in sorted(out.glob('*.csv'))})
    dump(out/'summary.json', s)
    print(main_r.round(4).to_string(index=False)); print(json.dumps(s, indent=1))


if __name__ == '__main__':
    main()
