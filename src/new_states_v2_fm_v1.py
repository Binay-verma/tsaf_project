"""TimesFM-3 on the second-test states (EXPLORATORY; prediction committed before any run).

Checks out of sample, on the seven second-test states, the exploratory first-test finding that TimesFM-3 does better
with typed day flags than with a pooled day flag at leads 7 and 14 (results/new_states_v1_fm_control). Same pinned
weights, runner (ziel_foundation_v1), calendar base, cases and ledgers as the registered second test
(results/new_states_v2); arms: day5 (typed) and pooled1 (the pooled flag without zero padding). Not part of the
registered second test (osf.io/f9tv4), which used local models only.
Prediction: results/new_states_v2_fm/PREDICTION.md.

Kaggle (docs/reproduction/NEW_STATES_V2_FM_KAGGLE.md):
  python src/new_states_v2_fm_v1.py prepare            (local, committed before the run)
  python src/new_states_v2_fm_v1.py weights --cohort C
  python src/new_states_v2_fm_v1.py run --cohort C      (C = fm_2017_2020 or fm_2021_2025)
Then locally: python src/new_states_v2_fm_v1.py analyse
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
import new_states_v2 as s                 # noqa: E402  (patches the shared modules to the seven second-test states)
import longer_panel_stage_a_v1 as A       # noqa: E402
from festival_feature_design import sha, dump  # noqa: E402

OUT = ROOT/'results/new_states_v2_fm'
ARMS = ['day5', 'pooled1']
COHORTS = {'fm_2017_2020': [2017, 2018, 2019, 2020], 'fm_2021_2025': [2021, 2022, 2023, 2024, 2025]}
INPUTS = ['src/new_states_v2_fm_v1.py', 'src/new_states_v2.py', 'src/longer_panel_stage_a_v1.py', 'src/breadth_model_engine_v1.py',
          'src/ziel_foundation_v1.py', 'src/forecasting.py', 'src/extended_validation.py', 'src/festival_feature_design.py',
          'data/external/new_states_v2_energy_GWh.csv', 'results/new_states_v2/anchors_2015_2025.csv',
          'results/new_states_v2/placebo_anchors_2015_2025.csv', 'results/new_states_v2_fm/PREDICTION.md',
          'results/mechanism_controls_v1/chronos_download.json', 'results/second_model_audit_v1/weight_download.json']


def frames_fn(a, fake):
    def f(index, state):
        fr = A.frames(index, state, a, fake)
        pooled = fr['pooled_day5']
        return {'day5': fr['day5'], 'pooled1': pooled[[c for c in pooled.columns if not c.startswith('padding_')]]}
    return f


def prepare():
    parent = json.loads((ROOT/'results/feature_breadth_v1/event_window/protocol.json').read_text())
    ev = pd.read_csv(s.OUT/'event_window/primary_cases.csv')
    for c, years in COHORTS.items():
        d = OUT/c; d.mkdir(parents=True, exist_ok=False)
        cases = ev[ev.year.isin(years)].reset_index(drop=True)
        for f in ['primary_cases.csv', 'window_cases.csv']:
            cases.to_csv(d/f, index=False)
        dump(d/'protocol.json', dict(experiment=f'new_states_v2_fm/{c}', created_utc=datetime.now(timezone.utc).isoformat(), author='Binay Verma',
             status='EXPLORATORY; prediction committed before any run; not part of the registered second test.', states=list(s.NEW_STATES),
             arms=ARMS, models=['timesfm'], threads=parent['threads'], seed=parent['seed'], batch=parent['batch'],
             expected_tasks=int(len(cases[['state', 'year', 'origin']].drop_duplicates())),
             input_hashes={f: sha(ROOT/f) for f in INPUTS}, design_hashes={f: sha(d/f) for f in ['primary_cases.csv', 'window_cases.csv']}))
        print(c, len(cases), int(len(cases[['state', 'year', 'origin']].drop_duplicates())))


def weights(cohort):
    import ziel_foundation_v1 as zf
    zf.OUT = OUT/cohort          # one identity file per cohort, so two hosted runs never write the same file
    zf.weights()


def run(cohort):
    import breadth_model_engine_v1 as engine
    import ziel_foundation_v1 as zf
    a = pd.read_csv(s.OUT/s.LEDGER); fake = pd.read_csv(s.OUT/s.PLACEBO)
    engine.OUT = OUT/cohort; engine.ARMS = ARMS; engine.EXTRA = []; engine.ledger_bound = s.bound
    fr = frames_fn(a, fake); engine.frames = fr
    zf.OUT = OUT/cohort; zf.ARMS = ARMS; zf.frames = fr
    zf.foundation(engine, 'timesfm')


def analyse():
    import new_states_v2_analysis as an
    parts = []
    for c in COHORTS:
        b = OUT/c/'timesfm'
        r = json.loads((b/'run.json').read_text())
        assert sha(b/'predictions.csv') == r['predictions_sha256']
        parts.append(pd.read_csv(b/'predictions.csv'))
    d = pd.concat(parts, ignore_index=True)
    d['MASE'] = (d.prediction-d.actual).abs()/d.mase_scale
    rows = []
    for name, hz in [('lead 1', [1]), ('lead 7', [7]), ('lead 14', [14]), ('leads 7 and 14', [7, 14])]:
        x = d[d.horizon.isin(hz)]
        cell = x.groupby(['family', 'year', 'state', 'arm']).MASE.mean().unstack('arm')
        c = (cell['day5']-cell['pooled1']).groupby(['family', 'year']).mean()
        yv = c.groupby(level='year').mean()
        rows.append(dict(contrast=f'typed - pooled1, {name}', clusters=len(c), mean=float(c.mean()), years_negative=int((yv < 0).sum()), years=len(yv),
                         p_one_sided_typed_better=an.signflip(c.values, -1), p_one_sided_pooled_better=an.signflip(c.values, +1)))
    res = pd.DataFrame(rows)
    (OUT/'analysis').mkdir(exist_ok=False)
    res.to_csv(OUT/'analysis/contrasts.csv', index=False)
    print(res.round(4).to_string(index=False))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('action', choices=['prepare', 'weights', 'run', 'analyse'])
    ap.add_argument('--cohort', choices=list(COHORTS))
    x = ap.parse_args()
    if x.action == 'prepare':
        prepare()
    elif x.action == 'analyse':
        analyse()
    else:
        assert x.cohort, '--cohort required'
        (weights if x.action == 'weights' else run)(x.cohort)
